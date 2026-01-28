import os

from dotenv import load_dotenv

load_dotenv(override=False)

# 공통 설정
REMOTE_HOST = os.getenv("REMOTE_HOST")

# RDB 설정
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DB_HOST = os.getenv("DB_HOST", REMOTE_HOST)
DB_PORT = int(os.getenv("DB_PORT"))

# REDIS
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

REDIS_HOST = os.getenv("REDIS_HOST", REMOTE_HOST)
REDIS_PORT = os.getenv("REDIS_PORT")

# LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# services
BE_ROUTER_HOST = os.getenv("BE_ROUTER_HOST", REMOTE_HOST)
BE_ROUTER_PORT = os.getenv("BE_ROUTER_PORT")

GM_HOST = os.getenv("GM_HOST", REMOTE_HOST)
GM_PORT = os.getenv("GM_PORT")

SCENARIO_SERVICE_HOST = os.getenv("SCENARIO_SERVICE_HOST", REMOTE_HOST)
SCENARIO_SERVICE_PORT = os.getenv("SCENARIO_SERVICE_PORT")

STATE_MANAGER_HOST = os.getenv("STATE_MANAGER_HOST", REMOTE_HOST)
STATE_MANAGER_PORT = os.getenv("STATE_MANAGER_PORT")

LLM_GATEWAY_HOST = os.getenv("LLM_GATEWAY_HOST", REMOTE_HOST)
LLM_GATEWAY_PORT = os.getenv("LLM_GATEWAY_PORT")

WEB_HOST = os.getenv("WEB_HOST", REMOTE_HOST)
WEB_PORT = os.getenv("WEB_PORT")

# 원격 서버
APP_HOST = os.getenv("APP_HOST")  # 운영 환경에서는 '0.0.0.0' 주입
APP_PORT = int(os.getenv("APP_PORT"))
APP_ENV = os.getenv("APP_ENV")  # local, dev, prod 등
# 웹
WEB_PORT = os.getenv("WEB_PORT")
