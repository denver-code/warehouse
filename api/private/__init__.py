from fastapi import APIRouter
from api.private.warehouse import warehouse_router


private_router = APIRouter(prefix="/private")

private_router.include_router(warehouse_router)
