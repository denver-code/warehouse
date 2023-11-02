from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from app.schemas.warehouse import NewItem
from app.models.warehouse import Storage, Container, PermissionRole, Location, Item
from app.core.authorization import auth_required
from os import path as os_path


item_router = APIRouter()


@item_router.post("/item")
async def create_item(
    payload: NewItem,
    user: dict = Depends(auth_required),
):
    container = await Container.find_one(Container.code == payload.container_code)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    location_code = (
        await Storage.find_one(Storage.code == container.storage_code)
    ).location_code

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location_code,
        PermissionRole.role == "admin" or PermissionRole.role == "editor",
    )

    if not user_role:
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to create an item in this container",
        )

    item = await Item.create(Item(**payload.model_dump()))
    return item


@item_router.get("/item/{itemid}")
async def get_item(itemid, user: dict = Depends(auth_required)):
    item = await Item.get(itemid)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    container = await Container.find_one(Container.code == item.container_code)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    location_code = (
        await Storage.find_one(Storage.code == container.storage_code)
    ).location_code

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location_code,
    )
    if not user_role or user_role.role not in ["admin", "editor", "viewer"]:
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to view this item",
        )

    item = item.model_dump()

    if os_path.isfile(f"static/{item['id']}.jpg"):
        item["has_picture"] = True
    else:
        item["has_picture"] = False

    return item


@item_router.get("/item/{itemid}/picture")
async def get_item_picture(itemid, user: dict = Depends(auth_required)):
    item = await Item.get(itemid)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    container = await Container.find_one(Container.code == item.container_code)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    location_code = (
        await Storage.find_one(Storage.code == container.storage_code)
    ).location_code

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location_code,
    )
    if not user_role or user_role.role not in ["admin", "editor", "viewer"]:
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to view this item",
        )

    if os_path.isfile(f"static/{item.id}.jpg"):
        return FileResponse(f"static/{item.id}.jpg")
    else:
        raise HTTPException(status_code=404, detail="Picture not found")


@item_router.patch("/item/{itemid}/picture")
async def set_item_picture(
    itemid, picture: UploadFile = File(None), user: dict = Depends(auth_required)
):
    item = await Item.get(itemid)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    container = await Container.find_one(Container.code == item.container_code)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    location_code = (
        await Storage.find_one(Storage.code == container.storage_code)
    ).location_code

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location_code,
        PermissionRole.role == "admin" or PermissionRole.role == "editor",
    )
    if not user_role:
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to set the picture of this item",
        )

    if picture:
        with open(f"static/{item.id}.jpg", "wb") as buffer:
            buffer.write(await picture.read())

    return {"message": "Picture set successfully"}


@item_router.get("/location/{location}/storage/{storage}/container/{code}/items")
async def get_items(
    location,
    storage,
    code,
    user: dict = Depends(auth_required),
):
    location = await Location.find_one(Location.code == location)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    storage = await Storage.find_one(
        Storage.code == storage, Storage.location_code == location.code
    )
    if not storage:
        raise HTTPException(status_code=404, detail="Storage not found")

    container = await Container.find_one(
        Container.code == code, Container.storage_code == storage.code
    )
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location.code,
    )
    if not user_role or user_role.role not in ["admin", "editor", "viewer"]:
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to view this container",
        )

    items = []

    async for item in Item.find(Item.container_code == container.code):
        item = item.model_dump()
        if os_path.isfile(f"static/{item['id']}.jpg"):
            item["has_picture"] = True
        else:
            item["has_picture"] = False
        items.append(item)

    return items
