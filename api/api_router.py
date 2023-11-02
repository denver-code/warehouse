from fastapi import APIRouter
from api.private import private_router


api_router = APIRouter(prefix="/api")
api_router.include_router(private_router)
