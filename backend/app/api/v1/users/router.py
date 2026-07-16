"""Users router with placeholder endpoints (Phase 1.2)."""

from fastapi import APIRouter

from app.schemas.common import BaseResponse, ResponseStatus

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=BaseResponse)
async def get_current_user() -> BaseResponse:
    """Retrieve the currently authenticated user's profile.

    Phase 1.2 - User service implementation pending.
    """
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Get current user - Phase 1.2 implementation pending",
        data={
            "id": "placeholder-user-id",
            "email": "user@example.com",
            "name": "Placeholder User",
        },
    )


@router.put("/me", response_model=BaseResponse)
async def update_current_user() -> BaseResponse:
    """Update the currently authenticated user's profile.

    Phase 1.2 - User service implementation pending.
    """
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Update current user - Phase 1.2 implementation pending",
    )


@router.get("/{user_id}", response_model=BaseResponse)
async def get_user(user_id: str) -> BaseResponse:
    """Retrieve a user by their unique identifier.

    Phase 1.2 - User service implementation pending.

    Args:
        user_id: The UUID of the user to retrieve.
    """
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Get user {user_id} - Phase 1.2 implementation pending",
    )
