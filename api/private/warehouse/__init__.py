from fastapi import APIRouter
from . import location, item, container, storage


warehouse_router = APIRouter(prefix="/warehouse")

warehouse_router.include_router(location.location_router)
warehouse_router.include_router(storage.storage_router)
warehouse_router.include_router(container.container_router)
warehouse_router.include_router(item.item_router)
