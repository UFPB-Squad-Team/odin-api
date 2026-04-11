from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from src.domain.exeptions.validation_error import DomainValidationError


def _build_error_payload(error_code: str, message: str, detail=None) -> dict:
    payload = {
        "error": error_code,
        "message": message,
    }
    if detail is not None:
        payload["detail"] = detail
    return payload


async def _http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    error_code = "HTTP_ERROR"
    if exc.status_code == 404:
        error_code = "NOT_FOUND"
    elif exc.status_code == 422:
        error_code = "VALIDATION_ERROR"
    elif exc.status_code >= 500:
        error_code = "INTERNAL_SERVER_ERROR"

    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_payload(error_code, str(exc.detail)),
    )


async def _request_validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_build_error_payload("VALIDATION_ERROR", "Invalid request payload", exc.errors()),
    )


async def _domain_validation_exception_handler(
    _: Request,
    exc: DomainValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_build_error_payload("DOMAIN_VALIDATION_ERROR", str(exc)),
    )


async def _mongo_exception_handler(_: Request, exc: PyMongoError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content=_build_error_payload(
            "DATABASE_ERROR",
            "The database is temporarily unavailable",
            str(exc),
        ),
    )


async def _value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_build_error_payload("MAPPER_ERROR", str(exc)),
    )


async def _generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_build_error_payload("INTERNAL_SERVER_ERROR", "An unexpected error occurred", str(exc)),
    )


def register_global_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _request_validation_exception_handler)
    app.add_exception_handler(DomainValidationError, _domain_validation_exception_handler)
    app.add_exception_handler(PyMongoError, _mongo_exception_handler)
    app.add_exception_handler(ValueError, _value_error_handler)
    app.add_exception_handler(Exception, _generic_exception_handler)
