"""Shared utilities, models, middleware, and error handlers for microservices."""

import logging
import uuid
from typing import Any, Generic, Optional, TypeVar
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("talent_gateway")

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class StandardResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Log incoming request
        print(f"[{request_id}] {request.method} {request.url.path}", flush=True)

        response = await call_next(request)

        # Set response header
        response.headers["X-Request-ID"] = request_id

        # Log completion
        print(f"[{request_id}] completed {response.status_code}", flush=True)

        return response


def setup_common_handlers(app: FastAPI):
    """Register middleware and uniform exception handlers on a FastAPI application."""
    app.add_middleware(RequestIdMiddleware)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = getattr(request.state, "request_id", "system")
        errors = exc.errors()
        messages = []
        for err in errors:
            loc = " -> ".join(str(l) for l in err.get("loc", []) if l != "body")
            msg = err.get("msg", "Invalid value")
            messages.append(f"{loc}: {msg}" if loc else msg)
        err_msg = "; ".join(messages) if messages else "Invalid request payload"

        return JSONResponse(
            status_code=422,
            headers={"X-Request-ID": req_id},
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": err_msg
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        req_id = getattr(request.state, "request_id", "system")
        return JSONResponse(
            status_code=exc.status_code,
            headers={"X-Request-ID": req_id},
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail)
                }
            }
        )
