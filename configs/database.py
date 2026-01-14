from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from configs.setting import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Engine 생성 (echo=True로 설정 시 쿼리 로그 확인 가능)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

# SessionLocal 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_db_connection():
    try:
        # Engine에서 연결을 맺고 테스트 쿼리 실행
        with engine.connect() as connection:
            # 간단한 테스트 쿼리
            connection.execute(text("SELECT 1"))

        # 성공 로그 출력
        print("✅ 데이터베이스와 연결되었습니다.")

    except OperationalError as e:
        # 연결 정보 오류 (잘못된 비밀번호, 포트 등)
        print(f"❌ 데이터베이스 연결 실패 (OperationalError): {e}")
        # 이 시점에서 서버 실행을 중단하려면 raise e 를 사용할 수 있습니다.

    except SQLAlchemyError as e:
        # 기타 SQLAlchemy 오류
        print(f"❌ 데이터베이스 연결 검사 도중 오류 발생: {e}")

    except Exception as e:
        # 예상치 못한 기타 오류
        print(f"❌ 예상치 못한 오류 발생: {e}")


# DB 세션을 제공하는 의존성 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

check_db_connection() # DB 연결 상태 검사