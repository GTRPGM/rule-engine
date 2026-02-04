import sys

import redis

from configs.setting import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from src.utils.logger import logger

# Redis 클라이언트 초기화
redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,  # 데이터를 문자열로 자동 디코딩
)


def check_redis_connection():
    try:
        redis_client.ping()
        logger.info("✅ Redis 서버와 성공적으로 연결되었습니다.")
    except redis.exceptions.ConnectionError as e:
        logger.error(
            f"❌ Redis 서버 연결에 실패했습니다. 다음을 확인하세요: {REDIS_HOST}:{REDIS_PORT} - {e}",
            exc_info=True,
        )
        sys.exit(1)  # Redis 연결 실패 시 애플리케이션 즉시 종료
    except Exception as e:
        logger.error(f"❌ Redis 연결 확인 중 예상치 못한 오류 발생: {e}", exc_info=True)
        sys.exit(1)  # 예상치 못한 오류 발생 시 애플리케이션 즉시 종료


def get_redis_client():
    try:
        # 연결 테스트
        redis_client.ping()
        return redis_client
    except redis.exceptions.ConnectionError as e:
        logger.error(f"❌ Redis 클라이언트 요청 중 연결 오류 발생: {e}", exc_info=True)
        raise ConnectionError(
            "Redis 서버에 연결할 수 없습니다. 설정을 확인하거나 서버 상태를 점검하세요."
        ) from e
    except Exception as e:
        logger.error(
            f"❌ Redis 클라이언트 요청 중 예상치 못한 오류 발생: {e}", exc_info=True
        )
        raise RuntimeError(
            "Redis 클라이언트 사용 중 예상치 못한 오류가 발생했습니다."
        ) from e


check_redis_connection()
