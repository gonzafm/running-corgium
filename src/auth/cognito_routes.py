"""Auth routes for AWS mode (Cognito via API Gateway)."""

from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user

router = APIRouter(tags=["users"])


@router.get("/users/me")
async def users_me(user: dict[str, str] = Depends(get_current_user)):
    """Get current user info from Cognito claims."""
    return {
        "id": 0,
        "email": user["email"],
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
    }
