from datetime import datetime

from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    google_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    picture: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserCreate(schemas.BaseUserCreate):
    google_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    picture: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    picture: str | None = None
