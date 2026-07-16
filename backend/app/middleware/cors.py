"""CORS middleware configuration."""

from fastapi.middleware.cors import CORSMiddleware


def get_cors_middleware(
    allowed_origins: list[str],
) -> CORSMiddleware:
    """Create and return a configured CORS middleware instance.

    Args:
        allowed_origins: List of origins allowed to make cross-origin requests.

    Returns:
        A ``CORSMiddleware`` instance ready to be added to the application.
    """
    return CORSMiddleware(
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-Total-Count",
            "X-Total-Pages",
        ],
    )
