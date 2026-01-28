import redis

from configs.setting import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT

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
        print("✅ Redis 서버와 연결되었습니다.")
    except redis.exceptions.ConnectionError as e:
        print(f"⚠️ Redis 서버 연결에 실패했습니다: {e}")


def get_redis_client():
    try:
        # 연결 테스트
        redis_client.ping()
        return redis_client
    except redis.exceptions.ConnectionError as e:
        print(f"Redis 연결 실패: {e}")
        # 운영 환경에서는 서버 시작을 중단하거나 적절한 오류 처리 추가 고려
        raise e


check_redis_connection()
