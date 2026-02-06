import sys
from contextlib import contextmanager

import psycopg2
from fastapi import HTTPException
from psycopg2 import extras, pool

from src.configs.setting import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from src.utils.logger import logger

# 커넥션 풀 설정
try:
    connection_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=20,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
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
