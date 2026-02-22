from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.core.exceptions.base import (
    DomainException,
    NotFoundException,
    ConflictException
)
from src.core.exceptions.profile import NoMoreProfilesException


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    status_code = status.HTTP_400_BAD_REQUEST
    message = str(exc)
    
    if isinstance(exc, NotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ConflictException):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, NoMoreProfilesException):
        status_code = status.HTTP_404_NOT_FOUND
    
    return JSONResponse(
        status_code=status_code,
        content={"error": type(exc).__name__, "message": message}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "ValidationError", "message": exc.errors()}
    )


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)