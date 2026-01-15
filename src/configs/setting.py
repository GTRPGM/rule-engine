import os
from dotenv import load_dotenv

load_dotenv()

# DB 설정
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
APP_HOST = os.getenv("APP_HOST") # 운영 환경에서는 '0.0.0.0' 주입
APP_PORT = int(os.getenv("APP_PORT"))
APP_ENV = os.getenv("APP_ENV")  # local, dev, prod 등
