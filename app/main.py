from beanie import init_beanie
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.authorization import auth_required
from api.api_router import api_router
from app.core.config import settings
from app.core.db import db
from app.models.warehouse import *


def get_application():
    _app = FastAPI(title=settings.PROJECT_NAME)

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()


@app.on_event("startup")
async def on_startup():
    await init_beanie(
        database=db,
        document_models=[
            Location,
            PermissionRole,
            Storage,
            Container,
            Item,
        ],
    )


@app.get("/")
def root(user: dict = Depends(auth_required)):
    return {"message": f"Hello World from protected, {user['username']}!"}


app.include_router(api_router)
