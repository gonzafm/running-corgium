"""Auth routes for standalone mode (fastapi-users with SQLAlchemy)."""

from fastapi import APIRouter, Depends

from src.auth import auth_backend, current_active_user, fastapi_users
from src.auth.schemas import UserCreate, UserRead, UserUpdate
from src.database.models import User

router = APIRouter()


def register_standalone_auth_routes(app):
    """Register all fastapi-users authentication routes."""
    app.include_router(
        fastapi_users.get_auth_router(auth_backend),
        prefix="/auth/jwt",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_reset_password_router(),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_verify_router(UserRead),
        prefix="/auth",
        tags=["auth"],
    )
    app.include_router(
        fastapi_users.get_users_router(UserRead, UserUpdate),
        prefix="/users",
        tags=["users"],
    )


@router.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    """Example authenticated endpoint for standalone mode."""
    return {"message": f"Hello {user.email}!"}
