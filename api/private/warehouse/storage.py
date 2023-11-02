from fastapi import APIRouter, Depends, HTTPException
from app.core.authorization import auth_required
from app.core.validate_code import validate_code
from app.models.warehouse import Storage, Location, PermissionRole, Container
from app.schemas.warehouse import NewStorage


storage_router = APIRouter()


@storage_router.post("/storage")
async def create_storage(payload: NewStorage, user: dict = Depends(auth_required)):
    location = await Location.find_one(Location.code == payload.location_code)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location.code,
        PermissionRole.role == "admin",
    )
    if not user_role:
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to create storage in this location",
        )

    code = validate_code(payload.code)
    if code is None:
        raise HTTPException(status_code=400, detail="Invalid storage code")

    if await Storage.find_one(
        Storage.code == code, Storage.location_code == location.code
    ):
        raise HTTPException(status_code=400, detail="Storage already exists")

    storage = await Storage.create(Storage(**payload.model_dump()))

    return storage


@storage_router.get("/location/{location}/storage/{code}")
async def get_storage(location, code, user: dict = Depends(auth_required)):
    storage = await Storage.find_one(Storage.code == code)
    if not storage:
        raise HTTPException(status_code=404, detail="Storage not found")

    location = await Location.find_one(Location.code == location)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location.code,
    )
    if not user_role or user_role.role not in ["admin", "editor", "viewer"]:
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to view this storage",
        )

    containers = []

    async for container in Container.find(Container.storage_code == code):
        container = container.model_dump()
        to_delete = [
            "id",
            "storage_code",
        ]
        for key in to_delete:
            del container[key]
        containers.append(container)

    storage = storage.model_dump()
    storage["containers"] = containers

    return storage
