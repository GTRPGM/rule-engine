import sys
from contextlib import contextmanager

import psycopg2
from fastapi import HTTPException
from psycopg2 import extras, pool
from sshtunnel import SSHTunnelForwarder

from src.configs.setting import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    SSH_ENABLED,
    SSH_HOST,
    SSH_KEY_PATH,
    SSH_USER,
)
from src.utils.logger import logger

# RDB SSH 터널 정의
rdb_tunnel = None
actual_db_port = DB_PORT

if SSH_ENABLED:
    rdb_tunnel = SSHTunnelForwarder(
        (SSH_HOST, 22),
        ssh_username=SSH_USER,
        ssh_pkey=SSH_KEY_PATH,
        remote_bind_address=('127.0.0.1', DB_PORT),
        local_bind_address=('127.0.0.1', 0)
    )
    rdb_tunnel.start()
    actual_db_port = rdb_tunnel.local_bind_port
    logger.info(f"🚀 PostgreSQL용 SSH 터널 활성화 (Port: {actual_db_port})")

# 커넥션 풀 설정
try:
    connection_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=20,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=actual_db_port,
        database=DB_NAME,
    )
    logger.info("✅ 데이터베이스 커넥션 풀이 성공적으로 생성되었습니다.")
except Exception as e:
    logger.error(
        f"❌ 데이터베이스 커넥션 풀 생성 중 치명적인 오류 발생: {e}", exc_info=True
    )
    sys.exit(1)  # 커넥션 풀 생성 실패 시 애플리케이션 즉시 종료


# DB 연결 관리 Context Manager
def get_db_cursor():
    """
    커넥션 풀에서 커넥션을 빌려오고,
    결과를 딕셔너리 형태로 반환하는 커서(DictCursor)를 제공합니다.
    """
    conn = None  # conn을 None으로 초기화합니다.
    try:
        # 터널이 살아있는지 먼저 확인 (디버깅용)
        if SSH_ENABLED and (not rdb_tunnel or not rdb_tunnel.is_active):
            raise ConnectionError("RDB SSH 터널이 활성화되어 있지 않습니다.")

        conn = connection_pool.getconn()
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
        yield cursor
        conn.commit()
    except HTTPException:
        # FastAPI의 HTTPException은 그대로 다시 던집니다 (404 등을 유지하기 위해)
        raise
    except psycopg2.OperationalError as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ 데이터베이스 연결 또는 운영 오류 발생: {e}", exc_info=True)
        raise ConnectionError(
            "데이터베이스 연결 또는 운영 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        ) from e
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ 데이터베이스 쿼리 실행 중 오류 발생: {e}", exc_info=True)
        raise RuntimeError("데이터베이스 쿼리 실행 중 오류가 발생했습니다.") from e
    except Exception as e:
        if conn:
            conn.rollback()

        # 만약 e가 이미 HTTPException이라면 로깅하지 않고 그대로 던짐
        if isinstance(e, HTTPException):
            raise e

        logger.error(
            f"❌ 데이터베이스 커서 사용 중 예상치 못한 오류 발생: {e}", exc_info=True
        )
        raise RuntimeError(
            "데이터베이스 사용 중 예상치 못한 오류가 발생했습니다."
        ) from e
    finally:
        if conn:
            connection_pool.putconn(conn)


db_cursor_context = contextmanager(get_db_cursor)


# 연결 테스트
def check_db_connection():
    try:
        with db_cursor_context() as cursor:
            cursor.execute("SELECT 1")
            logger.info("✅ 데이터베이스 연결 상태 확인 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 확인 실패: {e}", exc_info=True)


check_db_connection()
