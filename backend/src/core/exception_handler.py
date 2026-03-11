from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ValidationException
from src.core.exceptions.base import (
    DomainException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    UnauthorizedException
)

EXCEPTION_STATUS_MAP = {
    NotFoundException: status.HTTP_404_NOT_FOUND,
    ConflictException: status.HTTP_409_CONFLICT,
    ForbiddenException: status.HTTP_403_FORBIDDEN,
    UnauthorizedException: status.HTTP_401_UNAUTHORIZED,
    ValidationException: status.HTTP_400_BAD_REQUEST,
}

async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    status_code = status.HTTP_400_BAD_REQUEST
    
    for exc_class, code in EXCEPTION_STATUS_MAP.items():
        if isinstance(exc, exc_class):
            status_code = code
            break
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "code": getattr(exc, 'code', None)
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "ValidationError", "message": exc.errors()}
    )


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
