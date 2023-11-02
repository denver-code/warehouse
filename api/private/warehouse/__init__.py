from fastapi import APIRouter, Depends, HTTPException
from app.schemas.warehouse import NewLocation, NewStorage, NewContainer, NewItem
from app.models.warehouse import Location, Storage, Container, Item, PermissionRole
from app.core.authorization import auth_required
import re

warehouse_router = APIRouter(prefix="/warehouse")


def validate_code(code: str):
    code = code.replace(" ", "-")
    if re.match(r"^[A-Z]{1,4}-[0-9]{1,3}$", code):
        return code
    return None


@warehouse_router.post("/location")
async def create_location(payload: NewLocation, user: dict = Depends(auth_required)):
    code = validate_code(payload.code)
    if code is None:
        raise HTTPException(status_code=400, detail="Invalid location code")

    if await Location.find_one(Location.code == code):
        raise HTTPException(status_code=400, detail="Location already exists")

    location = await Location.create(Location(**payload.model_dump()))

    await PermissionRole.create(
        PermissionRole(
            user_id=user["sub"],
            location_code=location.code,
            role="admin"
        )
    )

    return location


@warehouse_router.get("/location/{code}")
async def get_location(code, user: dict = Depends(auth_required)):
    location = await Location.find_one(Location.code == code)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location.code
    )
    if not user_role or user_role.role not in ["admin", "editor", "viewer"]:
        raise HTTPException(status_code=403, detail="User does not have permission to view this location")

    return location


@warehouse_router.get("/location/{code}/export")
async def export_location(code, user: dict = Depends(auth_required)):
    location = await Location.find_one(Location.code == code)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location.code
    )

    if not user_role or user_role.role not in ["admin", "editor", "viewer"]:
        raise HTTPException(status_code=403, detail="User does not have permission to export this location")

    loc_exp = {
        "location": location,
        "storages": []
    }

    storages = await Storage.find(Storage.location_code == code)
    for storage in storages:
        containers = []
        containers_query = Container.find(Container.storage_code == storage.code)
        async for container in containers_query:
            items = [item async for item in Item.find(Item.container_code == container.code)]
            containers.append({"container": container, "items": items})
        loc_exp["storages"].append({"storage": storage, "containers": containers})

    return loc_exp


@warehouse_router.post("/storage")
async def create_storage(payload: NewStorage, user: dict = Depends(auth_required)):
    location = await Location.find_one(Location.code == payload.location_code)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location.code,
        PermissionRole.role == "admin"
    )
    if not user_role:
        raise HTTPException(status_code=403, detail="User does not have permission to create storage in this location")

    code = validate_code(payload.code)
    if code is None:
        raise HTTPException(status_code=400, detail="Invalid storage code")

    if await Storage.find_one(Storage.code == code, Storage.location_code == location.code):
        raise HTTPException(status_code=400, detail="Storage already exists")

    storage = await Storage.create(Storage(**payload.model_dump()))

    return storage


@warehouse_router.post("/container")
async def create_container(payload: NewContainer, user: dict = Depends(auth_required)):
    storage = await Storage.find_one(Storage.code == payload.storage_code)
    if not storage:
        raise HTTPException(status_code=404, detail="Storage not found")

    location_code = (await Storage.find_one(Storage.code == storage.code)).location_code
    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location_code,
        PermissionRole.role in ["admin", "editor"]
    )

    if not user_role:
        raise HTTPException(status_code=403, detail="User doesn't have permission to create container in this storage")

    code = validate_code(payload.code)
    if code is None:
        raise HTTPException(status_code=400, detail="Invalid container code")

    if await Container.find_one(Container.name == payload.name, Container.storage_code == storage.code):
        raise HTTPException(status_code=400, detail="Container already exists")

    container = await Container.create(Container(**payload.model_dump()))

    return container


@warehouse_router.post("/item")
async def create_item(payload: NewItem, user: dict = Depends(auth_required)):
    container = await Container.find_one(Container.code == payload.container_code)
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")

    location_code = (await Storage.find_one(Storage.code == container.storage_code)).location_code

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location_code,
        PermissionRole.role in ["admin", "editor"]
    )

    if not user_role:
        raise HTTPException(status_code=403, detail="User does not have permission to create an item in this container")

    item = await Item.create(Item(**payload.model_dump()))

    return item
