"""Unified auth dependencies that work for both standalone and AWS modes."""

from fastapi import Depends, HTTPException, Request

from src.config import settings

if settings.db_backend == "standalone":
    from src.auth import current_active_user as _standalone_user
    from src.database.models import User

    async def get_current_user(
        user: User = Depends(_standalone_user),
    ) -> dict[str, str]:
        """Extract user info from fastapi-users in standalone mode."""
        return {
            "sub": str(user.id),
            "email": user.email,
        }

else:
    # AWS mode: extract user identity from API Gateway/Cognito request context
    async def _get_cognito_user(request: Request) -> dict[str, str]:
        """Extract user claims from Mangum-populated API Gateway event."""
        claims: dict[str, str] = {}
        event = request.scope.get("aws.event", {})
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})

        if "claims" in authorizer:
            claims = authorizer["claims"]
        elif "jwt" in authorizer:
            claims = authorizer["jwt"].get("claims", {})

        if not claims:
            raise HTTPException(status_code=401, detail="Missing Cognito claims")

        return {
            "sub": claims.get("sub", ""),
            "email": claims.get("email", ""),
        }

    get_current_user = _get_cognito_user  # type: ignore[assignment]
