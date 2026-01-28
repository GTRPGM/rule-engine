import os

from dotenv import load_dotenv

load_dotenv(override=False)

# RDB 설정
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
REMOTE_HOST = os.getenv("REMOTE_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
# REDIS
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
# LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LANGCHAIN_GATEWAY_PORT = os.getenv("LANGCHAIN_GATEWAY_PORT")
# 원격 서버
APP_HOST = os.getenv("APP_HOST")  # 운영 환경에서는 '0.0.0.0' 주입
APP_PORT = int(os.getenv("APP_PORT"))
APP_ENV = os.getenv("APP_ENV")  # local, dev, prod 등
# 웹
WEB_PORT = os.getenv("WEB_PORT")
# 시나리오 작성자(서비스)
SCENARIO_SERVICE_PORT = os.getenv("SCENARIO_SERVICE_PORT")
# 상태 관리자
STATE_MANAGER_PORT = os.getenv("STATE_MANAGER_PORT")
