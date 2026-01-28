import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Request, status
from starlette.middleware.cors import CORSMiddleware

from configs.api_routers import API_ROUTERS
from configs.database import check_db_connection
from configs.exceptions import init_exception_handlers
from configs.redis_conn import check_redis_connection
from src.common.dtos.common_response import CustomJSONResponse
from src.configs.logging_config import LOGGING_CONFIG
from src.configs.setting import APP_ENV, APP_PORT, REMOTE_HOST, WEB_PORT

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 시작될 때 실행
    print("\n" + "⭐" * 40)
    print(f"  Swagger UI: http://127.0.0.1:{APP_PORT}/docs")
    print(f"  ReDoc:      http://127.0.0.1:{APP_PORT}/redoc")
    print("⭐" * 40 + "\n")

    yield  # 서버가 동작하는 지점

    # 서버가 종료될 때 실행 (필요 시 작성)
    print("룰 엔진을 종료 중...")

app = FastAPI(
    title="GTRPGM Rule Engine",
    description="GTRPGM 게임 진행의 Rule 위배여부를 판정해 재조정하는 엔진입니다.",
    version="1.0.0",
    default_response_class=CustomJSONResponse,
    servers=[
        {"url": "/", "description": "Auto (Current Host)"},
        {"url": f"http://localhost:{APP_PORT}", "description": "Local env"},
        {"url": f"http://{REMOTE_HOST}:{APP_PORT}", "description": "Dev env"},
    ],
    lifespan=lifespan
)

@app.middleware("http")
async def error_logging_middleware(request: Request, call_next):
    # 이제 에러 로그는 핸들러가 담당하므로 미들웨어는 통과만 시킵니다.
    response = await call_next(request)
    return response


# 커스덤 에러 핸들러 초기화
init_exception_handlers(app)

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
