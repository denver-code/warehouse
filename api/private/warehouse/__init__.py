from fastapi import APIRouter

warehouse_router = APIRouter(prefix="/warehouse")

# location: SITE-12
# storage: LOCKER
# container[OPTIONAL]: ToolBox-1
# item: Hammer
