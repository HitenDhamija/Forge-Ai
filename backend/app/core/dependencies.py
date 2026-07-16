"""Core dependencies for dependency injection."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Get the current authenticated user.

    In development mode, returns a mock user if no token is provided.
    In production, this would validate the JWT token.
    """
    # Development mode: return mock user
    return {
        "id": "dev-user-001",
        "email": "developer@forgeai.local",
        "name": "Developer",
        "role": "admin",
    }
