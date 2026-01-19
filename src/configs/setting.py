import os

from dotenv import load_dotenv

load_dotenv()

# DB 설정
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
REMOTE_HOST = os.getenv("REMOTE_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
# REDIS
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
# LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# 원격 서버
APP_HOST = os.getenv("APP_HOST")  # 운영 환경에서는 '0.0.0.0' 주입
APP_PORT = int(os.getenv("APP_PORT"))
APP_ENV = os.getenv("APP_ENV")  # local, dev, prod 등

# 인증 - JWT 인증 관련 설정
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7일 동안 유효
REFRESH_TOKEN_EXPIRE_SECONDS = (
    REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
)  # 7일 만료 (초단위)
