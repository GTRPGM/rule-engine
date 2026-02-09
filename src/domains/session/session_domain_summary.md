# Session 도메인 코드 분석 요약

## 1. 도메인 목적 및 역할
Session 도메인은 사용자 세션 관리를 담당합니다. 특정 사용자의 활성화되거나 삭제된 세션 목록을 조회하고, 새로운 세션을 추가하며, 기존 세션을 논리적으로 삭제(삭제됨으로 표시)하는 기능을 제공합니다. 이 도메인은 데이터베이스와의 상호작용을 통해 세션 정보를 영구적으로 관리합니다.

## 2. 코드 구조
Session 도메인은 라우터, 서비스, DTOs, 그리고 쿼리 파일들로 구성됩니다.

### 주요 구성 요소
-   **`session_router.py`**: 사용자 세션 관리에 대한 모든 API 엔드포인트를 정의하고, 클라이언트 요청을 `SessionService`로 라우팅합니다.
-   **`session_service.py`**: 사용자 세션의 조회, 추가, 삭제 등 핵심 비즈니스 로직을 담당합니다. 데이터베이스와 직접 상호작용하며, SQL 쿼리를 활용하여 세션 정보를 처리합니다. `user_sessions` 테이블이 존재하지 않을 경우에 대한 예외 처리 로직도 포함합니다.
-   **`dtos/session_dtos.py`**: `SessionRequest`, `SessionResponse`, `PaginatedSessionResponse` 등 Pydantic 모델을 정의하여 API 요청 및 응답 데이터 형식을 구조화합니다.
-   **`queries/`**: PostgreSQL 기반의 SQL 쿼리 파일들(`count_sessions.sql`, `del_session_by_session_id.sql`, `get_sessions.sql`, `insert_session.sql`)을 포함합니다. 이 파일들은 `SessionService`에서 데이터베이스 작업을 수행할 때 사용됩니다.

### 디렉토리 구조
```
src/domains/session/
├───dtos/
│   ├───session_dtos.py
│   └───__init__.py
├───queries/
│   ├───count_sessions.sql
│   ├───del_session_by_session_id.sql
│   ├───get_sessions.sql
│   ├───insert_session.sql
│   └───__init__.py
├───session_router.py
├───session_service.py
└───__init__.py
```

## 3. 로직 처리 흐름

### `session_router.py` (API 엔드포인트)
-   **`GET /session/list`**: `user_id`, `skip`, `limit`, `is_deleted` 파라미터를 받아 특정 사용자의 세션 목록을 페이지네이션하여 조회합니다. `SessionService.get_user_sessions` 메서드를 호출하여 세션 데이터와 페이지네이션 메타 정보를 반환합니다.
-   **`POST /session/add`**: `SessionRequest` 객체를 통해 사용자 ID와 세션 ID를 받아 새로운 사용자 세션을 추가합니다. `SessionService.add_user_session` 메서드를 호출하여 세션을 생성하고 `SessionResponse`를 반환합니다.
-   **`DELETE /session/delete`**: `SessionRequest` 객체에서 세션 ID를 받아 해당 세션을 논리적으로 삭제(데이터베이스에서 `is_deleted` 플래그를 `true`로 업데이트)합니다. `SessionService.del_user_session` 메서드를 호출하고 삭제된 세션의 ID를 반환합니다.

### `session_service.py` (세션 관리 로직)
1.  **초기화**: 데이터베이스 커서를 주입받아 `self.cursor`로 저장합니다. 필요한 SQL 쿼리 파일들을 `load_sql` 유틸리티 함수를 통해 미리 로드합니다.
2.  **`get_user_sessions`**:
    *   `count_sessions_sql`을 사용하여 전체 세션 수를 조회하고, `get_sessions_sql`을 사용하여 페이지네이션 조건에 맞는 세션 목록을 조회합니다.
    *   조회된 세션 데이터와 `PaginationMeta` 객체를 포함하는 튜플을 반환합니다.
    *   `user_sessions` 테이블이 존재하지 않을 경우를 대비하여 경고를 로깅하고 빈 결과를 반환하는 예외 처리 로직을 포함합니다.
3.  **`add_user_session`**:
    *   `insert_session_sql`을 사용하여 `SessionRequest`에 포함된 `user_id`와 `session_id`로 새로운 세션 레코드를 데이터베이스에 삽입합니다.
    *   `user_sessions` 테이블이 없을 경우 no-op 처리를 합니다.
    *   현재 시간으로 `created_at`을 설정한 `SessionResponse`를 반환합니다.
4.  **`del_user_session`**:
    *   `del_session_by_session_id_sql`을 사용하여 `SessionRequest`의 `session_id`에 해당하는 세션의 `is_deleted` 플래그를 `true`로 업데이트합니다.
    *   `user_sessions` 테이블이 없을 경우 no-op 처리를 합니다.
    *   삭제된 세션의 `session_id`를 반환합니다.
5.  **`_is_missing_user_sessions_table`**: 내부 헬퍼 함수로, 발생한 예외 메시지를 분석하여 `user_sessions` 테이블이 존재하지 않아서 발생한 에러인지 판단합니다.

## 4. 다른 서비스와의 연계

-   **데이터베이스**: PostgreSQL 데이터베이스와 직접 연동하여 사용자 세션 정보를 영구적으로 저장하고 관리합니다.
-   **`src/utils/load_sql.py`**: `SessionService`에서 필요한 SQL 쿼리 파일을 로드하는 데 사용됩니다.
-   **`src/utils/logger.py`**: 서비스 로직 내에서 경고 메시지를 로깅하는 데 사용됩니다.
-   **`common/dtos/pagination_meta.py`**: 세션 목록 조회 시 페이지네이션 메타 정보를 제공하는 데 사용됩니다.

## 5. 개발 원칙 준수
-   **객체지향 설계 (OOP)**: `SessionRouter`와 `SessionService` 모두 클래스 기반으로 구현되어 객체 지향 원칙을 따르며, 각 클래스는 명확한 책임과 메서드를 가집니다.
-   **코드 스타일 (Pythonic Code)**: 코드의 일관성과 가독성을 위해 파이썬 스타일 가이드 및 Ruff 린팅 규칙을 준수합니다.
-   **코드 품질 관리 (Linting)**: `pyproject.toml`에 정의된 Ruff 규칙을 통해 코드 품질이 관리됩니다.
-   **데이터 흐름 (Data Flow)**: Router -> Service 계층의 명확한 분리 및 데이터베이스 쿼리의 외부 파일 관리로 관심사를 분리합니다.
-   **Type Hinting**: 모든 메서드의 인자와 반환 값에 타입 힌트가 명시되어 개발 편의성과 코드 안정성을 높입니다.
