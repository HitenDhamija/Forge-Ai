"""FastAPI exception handlers that return consistent error responses."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.responses import JSONResponse

from app.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    ForgeBaseException,
    InternalServerException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)


async def _forge_exception_handler(
    request: Request, exc: ForgeBaseException
) -> JSONResponse:
    """Handle all ForgeBaseException subclasses.

    Maps custom exception types to appropriate HTTP status codes.
    """
    status_map: dict[type, int] = {
        NotFoundException: 404,
        BadRequestException: 400,
        UnauthorizedException: 401,
        ForbiddenException: 403,
        ConflictException: 409,
        ValidationException: 422,
        InternalServerException: 500,
    }
    status_code = status_map.get(type(exc), 500)
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "message": exc.message,
            "errors": None,
            "timestamp": None,
            "request_id": request_id,
        },
    )


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI request validation errors (422)."""
    request_id = getattr(request.state, "request_id", None)
    errors = []
    for error in exc.errors():
        loc = " -> ".join(str(item) for item in error["loc"])
        errors.append({"field": loc, "message": error["msg"]})
    return JSONResponse(
        status_code=422,
        content={
            "status": "validation_error",
            "message": "Validation error",
            "errors": errors,
            "timestamp": None,
            "request_id": request_id,
        },
    )


async def _pydantic_validation_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic ValidationError instances."""
    request_id = getattr(request.state, "request_id", None)
    errors = []
    for error in exc.errors():
        loc = " -> ".join(str(item) for item in error["loc"])
        errors.append({"field": loc, "message": error["msg"]})
    return JSONResponse(
        status_code=422,
        content={
            "status": "validation_error",
            "message": "Validation error",
            "errors": errors,
            "timestamp": None,
            "request_id": request_id,
        },
    )


async def _integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """Handle SQLAlchemy integrity constraint violations."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=409,
        content={
            "status": "error",
            "message": "A database integrity error occurred. The resource may already exist.",
            "errors": None,
            "timestamp": None,
            "request_id": request_id,
        },
    )


async def _sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle general SQLAlchemy errors."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "A database error occurred.",
            "errors": None,
            "timestamp": None,
            "request_id": request_id,
        },
    )


async def _unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all handler for unhandled exceptions."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected internal error occurred.",
            "errors": None,
            "timestamp": None,
            "request_id": request_id,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(ForgeBaseException, _forge_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(
        RequestValidationError, _validation_exception_handler
    )
    app.add_exception_handler(ValidationError, _pydantic_validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(IntegrityError, _integrity_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(SQLAlchemyError, _sqlalchemy_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_exception_handler)  # type: ignore[arg-type]
