from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from configs.api_routers import API_ROUTERS
from src.common.dtos.common_response import CustomJSONResponse
from src.configs.database import check_db_connection
from src.configs.logging_config import LOGGING_CONFIG
from src.configs.setting import APP_ENV, APP_PORT

app = FastAPI(
    title="GTRPGM Rule Engine",
    description="GTRPGM 게임 진행의 Rule 위배여부를 판정해 재조정하는 엔진입니다.",
    version="1.0.0",
    default_response_class=CustomJSONResponse,
)

# CORS 미들웨어 추가
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    f"http://localhost:{APP_PORT}",
    f"http://127.0.0.1:{APP_PORT}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 출처 목록
    allow_credentials=True,  # 쿠키 등 자격 증명 허용 여부
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

for router in API_ROUTERS:
    app.include_router(router)


@app.get("/", description="서버 연결 확인", summary="테스트 - 서버 연결을 확인합니다.")
def read_root():
    return {"message": "반갑습니다. GTRPGM 룰 엔진입니다!"}


if __name__ == "__main__":
    check_db_connection()
    # check_redis_connection() # 아직 고려 안 함
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
