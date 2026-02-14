import sys

import redis
from sshtunnel import SSHTunnelForwarder

from configs.setting import (
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    SSH_ENABLED,
    SSH_HOST,
    SSH_KEY_PATH,
    SSH_USER,
)
from src.utils.logger import logger

# Redis SSH 터널 정의
redis_tunnel = None

if SSH_ENABLED:
    try:
        redis_tunnel = SSHTunnelForwarder(
            (SSH_HOST, 22),
            ssh_username=SSH_USER,
            ssh_pkey=SSH_KEY_PATH,
            remote_bind_address=('127.0.0.1', REDIS_PORT),
            local_bind_address=('127.0.0.1', 0)
        )
        redis_tunnel.start()
        actual_port = redis_tunnel.local_bind_port
        logger.info(f"🚀 Redis용 SSH 터널이 활성화되었습니다. (Port: {actual_port})")
    except Exception as e:
        logger.error(f"❌ Redis SSH 터널 생성 실패: {e}")
        sys.exit(1)
    
# Redis 클라이언트 초기화
redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,  # 데이터를 문자열로 자동 디코딩
)

def check_redis_connection():
    try:
        # 터널이 살아있는지 먼저 확인 (디버깅용)
        if SSH_ENABLED and (not redis_tunnel or not redis_tunnel.is_active):
            raise ConnectionError("Redis SSH 터널이 활성화되어 있지 않습니다.")

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
