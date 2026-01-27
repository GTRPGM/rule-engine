import logging
import traceback
from typing import Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from configs.api_routers import API_ROUTERS
from configs.database import check_db_connection
from configs.redis_conn import check_redis_connection
from src.common.dtos.common_response import CustomJSONResponse
from src.configs.logging_config import LOGGING_CONFIG
from src.configs.setting import APP_ENV, APP_PORT, REMOTE_HOST, WEB_PORT

logger = logging.getLogger("uvicorn.error")


app = FastAPI(
    title="GTRPGM Rule Engine",
    description="GTRPGM 게임 진행의 Rule 위배여부를 판정해 재조정하는 엔진입니다.",
    version="1.0.0",
    default_response_class=CustomJSONResponse,
)


@app.middleware("http")
async def error_logging_middleware(request: Request, call_next):
    # 이제 에러 로그는 핸들러가 담당하므로 미들웨어는 통과만 시킵니다.
    response = await call_next(request)
    return response


# 1. 일반적인 모든 서버 에러 (500)
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


# 2. 의도된 HTTP 에러 (400, 401, 404, 503 등) - 중복 제거 및 통합
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # 이모지는 ⚠️를 써서 500 에러(🔥)와 구분하면 디버깅이 편합니다.
    logger.error(f"⚠️ HTTP {exc.status_code} Error: {request.method} {request.url.path}")
    logger.error(f"Detail: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": "요청 처리 중 오류가 발생했습니다.",
            "detail": exc.detail,
        },
    )


# 3. 데이터 검증 에러 (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
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


# CORS 미들웨어 추가
origins = [
    f"http://localhost:{WEB_PORT}",
    f"http://127.0.0.1:{WEB_PORT}",
    f"http://localhost:{APP_PORT}",
    f"http://127.0.0.1:{APP_PORT}",
    f"http://{REMOTE_HOST}:{APP_PORT}",
    f"http://{REMOTE_HOST}:{WEB_PORT}",
    f"http://{REMOTE_HOST}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처 목록
    allow_credentials=True,  # 쿠키 등 자격 증명 허용 여부
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)


def register_routers(app: FastAPI):
    for router in API_ROUTERS:
        app.include_router(router)


register_routers(app)


@app.get("/", description="서버 연결 확인", summary="테스트 - 서버 연결을 확인합니다.")
def read_root():
    return {"message": "반갑습니다. GTRPGM 룰 엔진입니다!"}


@app.get("/health")
def health_check() -> Dict[str, str]:
    health_status = {"status": "ok", "db": "connected", "redis": "connected"}
    try:
        check_db_connection()
        check_redis_connection()
        return health_status
    except Exception as e:
        # 하나라도 실패하면 503 에러 반환
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "message": str(e)},
        )


if __name__ == "__main__":
    import uvicorn

    effective_host = "127.0.0.1" if APP_ENV == "local" else "0.0.0.0"

    LOGGING_CONFIG["handlers"]["default"]["stream"] = "ext://sys.stdout"
    LOGGING_CONFIG["handlers"]["access"]["stream"] = "ext://sys.stdout"

    uvicorn.run(
        "main:app",
        host=effective_host,
        port=APP_PORT,
        reload=(APP_ENV == "local"),
        log_config=LOGGING_CONFIG,
    )
