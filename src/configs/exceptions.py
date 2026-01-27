import logging
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

logger = logging.getLogger("uvicorn.error")


def init_exception_handlers(app: FastAPI):
    """FastAPI 앱에 에러 핸들러들을 등록합니다."""

    @app.exception_handler(Exception)
    async def universal_exception_handler(request: Request, exc: Exception):
        logger.error(f"🔥 Unexpected Error: {request.method} {request.url.path}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "서버 내부 오류가 발생했습니다.",
                "detail": str(exc),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(
            f"⚠️ HTTP {exc.status_code} Error: {request.method} {request.url.path}"
        )
        logger.error(f"Detail: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": "요청 처리 중 오류가 발생했습니다.",
                "detail": exc.detail,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = exc.errors()
        error_details = []
        for error in errors:
            loc = " -> ".join([str(x) for x in error.get("loc", [])])
            msg = error.get("msg")
            inp = error.get("input")
            error_details.append(f"[{loc}] {msg} (Input: {inp})")

        full_message = " | ".join(error_details)
        logger.error(f"❌ Validation Error: {request.method} {request.url.path}")
        logger.error(f"Detail: {full_message}")

        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "message": "입력값 검증에 실패했습니다.",
                "detail": errors,
            },
        )
