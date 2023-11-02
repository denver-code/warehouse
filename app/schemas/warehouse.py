from pydantic import BaseModel


class NewLocation(BaseModel):
    code: str
    name: str
    description: str


class NewStorage(BaseModel):
    location_code: str
    code: str
    name: str
    description: str


class NewContainer(BaseModel):
    storage_code: str
    code: str
    name: str
    description: str


class NewItem(BaseModel):
    container_code: str
    name: str
    description: str


class NewRole(BaseModel):
    user_id: str
    location_code: str
    role: str
