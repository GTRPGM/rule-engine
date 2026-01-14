from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from configs.database import check_db_connection
from domains.common.dtos.common_response import CustomJSONResponse
from configs.logging_config import LOGGING_CONFIG

app = FastAPI(
    title="GTRPGM Rule Engine",
    description="GTRPGM의 게임 진행의 Rule 위배여부를 판정해 재조정하는 엔진입니다.",
    version="1.0.0",
    default_response_class=CustomJSONResponse,
)

# CORS 미들웨어 추가
origins = [
    "http://localhost:3000",    # Next.js 기본 개발 포트
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",    # 스웨거
    # 추후 프로덕션 환경의 프론트엔드 도메인도 여기에 추가
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # 허용할 출처 목록
    allow_credentials=True,         # 쿠키 등 자격 증명 허용 여부
    allow_methods=["*"],            # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],            # 모든 HTTP 헤더 허용
)

# 루트 경로 ("/")에 대한 GET 요청 처리 함수 (경로 연산)
@app.get("/", description="서버 연결 확인", summary="테스트 - 서버 연결을 확인합니다.")
def read_root():
    return {"message": "반갑습니다. GTRPGM 룰 엔진입니다!"}

if __name__ == "__main__":
    check_db_connection()
    import uvicorn

    LOGGING_CONFIG['handlers']['default']['stream'] = "ext://sys.stdout"
    LOGGING_CONFIG['handlers']['access']['stream'] = "ext://sys.stdout"

    # 서버를 코드 레벨에서 실행
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_config=LOGGING_CONFIG)