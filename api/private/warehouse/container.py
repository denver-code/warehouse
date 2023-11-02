from fastapi import APIRouter, Depends, HTTPException
from app.core.validate_code import validate_code
from app.schemas.warehouse import NewContainer
from app.models.warehouse import Storage, Container, PermissionRole, Location
from app.core.authorization import auth_required


container_router = APIRouter()


@container_router.post("/container")
async def create_container(payload: NewContainer, user: dict = Depends(auth_required)):
    storage = await Storage.find_one(Storage.code == payload.storage_code)
    if not storage:
        raise HTTPException(status_code=404, detail="Storage not found")

    location_code = (await Storage.find_one(Storage.code == storage.code)).location_code
    user_role = await PermissionRole.find_one(
        PermissionRole.user_id == user["sub"],
        PermissionRole.location_code == location_code,
        PermissionRole.role == "admin" or PermissionRole.role == "editor",
    )

    if not user_role:
        raise HTTPException(
            status_code=403,
            detail="User doesn't have permission to create container in this storage",
        )

    code = validate_code(payload.code)
    if code is None:
        raise HTTPException(status_code=400, detail="Invalid container code")

    if await Container.find_one(
        Container.name == payload.name, Container.storage_code == storage.code
    ):
        raise HTTPException(status_code=400, detail="Container already exists")

    container = await Container.create(Container(**payload.model_dump()))

    return container


@container_router.get("/location/{location}/storage/{storage}/container/{code}")
async def get_container(location, storage, code, user: dict = Depends(auth_required)):
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

    container = container.model_dump()

    return container
