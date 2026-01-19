from contextlib import contextmanager

from psycopg2 import extras, pool

from src.configs.setting import DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, REMOTE_HOST

# 커넥션 풀 설정
try:
    connection_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=20,
        user=DB_USER,
        password=DB_PASSWORD,
        host=REMOTE_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )
    print("✅ 커넥션 풀이 생성되었습니다.")
except Exception as e:
    print(f"❌ 커넥션 풀 생성 실패: {e}")


# DB 연결 관리 Context Manager
@contextmanager
def get_db_cursor():
    """
    커넥션 풀에서 커넥션을 빌려오고,
    결과를 딕셔너리 형태로 반환하는 커서(DictCursor)를 제공합니다.
    """
    conn = connection_pool.getconn()
    try:
        yield conn.cursor(cursor_factory=extras.RealDictCursor)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        connection_pool.getconn()
        connection_pool.putconn(conn)


# 연결 테스트
def check_db_connection():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ DB 연결 상태 확인 완료")
    except Exception as e:
        print(f"❌ DB 연결 확인 실패: {e}")


check_db_connection()
