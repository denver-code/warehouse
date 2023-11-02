from fastapi import APIRouter, Depends, HTTPException
from app.core.validate_code import validate_code
from app.schemas.warehouse import NewLocation
from app.models.warehouse import Location, Storage, Container, Item, PermissionRole
from app.core.authorization import auth_required


location_router = APIRouter()


@location_router.post("/location")
async def create_location(payload: NewLocation, user: dict = Depends(auth_required)):
    code = validate_code(payload.code)
    if code is None:
        raise HTTPException(status_code=400, detail="Invalid location code")

    if await Location.find_one(Location.code == code):
        raise HTTPException(status_code=400, detail="Location already exists")

    location = await Location.create(Location(**payload.model_dump()))

    await PermissionRole.create(
        PermissionRole(user_id=user["sub"], location_code=location.code, role="admin")
    )

    return location


@location_router.get("/location/{code}")
async def get_location(code, user: dict = Depends(auth_required)):
    location = await Location.find_one(Location.code == code)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location.code,
    )
    if not user_role or user_role.role not in ["admin", "editor", "viewer"]:
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to view this location",
        )

    storages = []

    async for storage in Storage.find(Storage.location_code == code):
        storage = storage.model_dump()
        to_delete = [
            "id",
            "location_code",
        ]
        for key in to_delete:
            del storage[key]
        storages.append(storage)

    location = location.model_dump()
    location["storages"] = storages

    return location


@location_router.get("/location/{code}/export")
async def export_location(code, user: dict = Depends(auth_required)):
    location = await Location.find_one(Location.code == code)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location.code,
    )

    if not user_role or user_role.role not in ["admin", "editor", "viewer"]:
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to export this location",
        )
    loc_exp = {
        "location": await Location.find_one(Location.code == code),
        "storages": [
            {
                "storage": storage,
                "containers": [
                    {
                        "container": container,
                        "items": [
                            item
                            async for item in Item.find(
                                Item.container_code == container.code
                            )
                        ],
                    }
                    async for container in Container.find(
                        Container.storage_code == storage.code
                    )
                ],
            }
            async for storage in Storage.find(Storage.location_code == code)
        ],
    }

    return loc_exp
