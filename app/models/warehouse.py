from beanie import Document, Indexed, init_beanie, UnionDoc
import pymongo


class Location(Document):
    code: Indexed(str, index_type=pymongo.TEXT)
    name: str
    description: str = None

    class Settings:
        name = "locations"


class PermissionRole(Document):
    user_id: Indexed(str, index_type=pymongo.TEXT)
    location_code: str
    role: str

    class Settings:
        name = "roles"


class Storage(Document):
    location_code: Indexed(str, index_type=pymongo.TEXT)
    code: str
    name: str
    description: str = None

    class Settings:
        name = "storages"


class Container(Document):
    storage_code: Indexed(str, index_type=pymongo.TEXT)
    code: str
    name: str
    description: str = None

    class Settings:
        name = "containers"


class Item(Document):
    container_code: Indexed(str, index_type=pymongo.TEXT)
    name: str
    description: str = None

    class Settings:
        name = "items"
