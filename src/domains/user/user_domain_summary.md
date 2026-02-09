# User 도메인 코드 분석 요약

## 1. 도메인 목적 및 역할
User 도메인은 사용자(회원) 관리 기능을 제공합니다. 회원 가입, 회원 정보 조회, 회원 정보 수정, 비밀번호 변경, 그리고 회원 탈퇴(논리적 삭제) 등 사용자 계정과 관련된 핵심 CRUD(Create, Read, Update, Delete) 작업을 담당합니다. 이 도메인은 데이터베이스와의 상호작용을 통해 사용자 정보를 영구적으로 관리합니다.

## 2. 코드 구조
User 도메인은 라우터, 서비스, DTOs, 그리고 쿼리 파일들로 구성됩니다.

### 주요 구성 요소
-   **`user_router.py`**: 사용자 계정 관리에 대한 모든 API 엔드포인트를 정의하고, 클라이언트 요청을 `UserService`로 라우팅합니다. 회원 가입, 정보 조회/수정, 비밀번호 변경, 회원 탈퇴 등의 엔드포인트를 포함합니다.
-   **`user_service.py`**: 사용자 계정의 생성, 조회, 수정, 삭제 등 핵심 비즈니스 로직을 담당합니다. 데이터베이스와 직접 상호작용하며, SQL 쿼리를 활용하여 사용자 정보를 처리합니다.
-   **`dtos/user_dtos.py`**: `UserCreateRequest`, `UserInfo`, `UserPWUpdateRequest`, `UserUpdateRequest` 등 Pydantic 모델을 정의하여 API 요청 및 응답 데이터 형식을 구조화합니다.
-   **`queries/`**: PostgreSQL 기반의 SQL 쿼리 파일들(`delete_user.sql`, `insert_user.sql`, `select_user.sql`, `update_user.sql`, `update_user_password.sql`)을 포함합니다. 이 파일들은 `UserService`에서 데이터베이스 작업을 수행할 때 사용됩니다.

### 디렉토리 구조
```
src/domains/user/
├───dtos/
│   ├───user_dtos.py
│   └───__init__.py
├───queries/
│   ├───delete_user.sql
│   ├───insert_user.sql
│   ├───select_user.sql
│   ├───update_user.sql
│   ├───update_user_password.sql
│   └───__init__.py
├───user_router.py
├───user_service.py
└───__init__.py
```

## 3. 로직 처리 흐름

### `user_router.py` (API 엔드포인트)
-   **`GET /user/{user_id}`**: 특정 `user_id`를 사용하여 회원 정보를 조회합니다. `UserService.get_user` 메서드를 호출하고, 조회된 `UserInfo`를 반환합니다. 사용자가 없을 경우 `404 NOT FOUND`를 반환합니다.
-   **`POST /user/create`**: `UserCreateRequest` 객체를 통해 새로운 사용자를 생성합니다. `UserService.create_user` 메서드를 호출하고, 생성된 `UserInfo`를 반환합니다.
-   **`PUT /user/update`**: `UserUpdateRequest` 객체를 통해 사용자 정보를 수정합니다. `UserService.update_user` 메서드를 호출하고, 업데이트된 `UserInfo`를 반환합니다. 회원 정보가 존재하지 않을 경우 `404 NOT FOUND`를 반환합니다.
-   **`PATCH /user/password`**: `UserPWUpdateRequest` 객체를 통해 사용자 비밀번호를 변경합니다. `UserService.update_user_password` 메서드를 호출하고, 변경된 사용자 ID를 반환합니다. 존재하지 않는 회원일 경우 `404 NOT FOUND`를 반환합니다.
-   **`DELETE /user/delete/{user_id}`**: 특정 `user_id`를 사용하여 회원을 탈퇴 처리합니다(논리적 삭제). `UserService.del_user` 메서드를 호출하고, 삭제된 사용자 ID를 반환합니다. 존재하지 않는 회원일 경우 `404 NOT FOUND`를 반환합니다.

### `user_service.py` (사용자 관리 로직)
1.  **초기화**: 데이터베이스 커서를 주입받아 `self.cursor`로 저장합니다. 필요한 SQL 쿼리 파일들을 `load_sql` 유틸리티 함수를 통해 미리 로드합니다.
2.  **`get_user`**: `select_user.sql` 쿼리를 사용하여 `user_id`에 해당하는 사용자 정보를 조회합니다. 조회된 데이터가 있으면 `UserInfo` 객체로 변환하여 반환하고, 없으면 `None`을 반환합니다.
3.  **`create_user`**: `insert_user.sql` 쿼리를 사용하여 `UserCreateRequest`의 데이터를 기반으로 새로운 사용자 레코드를 데이터베이스에 삽입합니다. 삽입 후 사용자 정보를 다시 조회하여 `UserInfo` 객체로 반환합니다. 실패 시 예외를 발생시킵니다.
4.  **`update_user`**: `update_user.sql` 쿼리를 사용하여 `UserUpdateRequest`의 데이터를 기반으로 사용자 정보를 업데이트합니다. 업데이트된 사용자 정보를 `UserInfo` 객체로 반환하고, 없으면 `None`을 반환합니다.
5.  **`update_user_password`**: `update_user_password.sql` 쿼리를 사용하여 `UserPWUpdateRequest`의 데이터를 기반으로 사용자 비밀번호를 업데이트합니다. 업데이트된 사용자의 `user_id`를 반환하고, 없으면 `None`을 반환합니다.
6.  **`del_user`**: `delete_user.sql` 쿼리를 사용하여 `user_id`에 해당하는 사용자를 논리적으로 삭제 처리합니다. 삭제된 사용자의 `user_id`를 반환하고, 없으면 `None`을 반환합니다.

## 4. 다른 서비스와의 연계

-   **데이터베이스**: PostgreSQL 데이터베이스와 직접 연동하여 사용자 정보를 영구적으로 저장하고 관리합니다.
-   **`src/utils/load_sql.py`**: `UserService`에서 필요한 SQL 쿼리 파일을 로드하는 데 사용됩니다.
-   **`common/dtos/wrapped_response.py`**: API 응답을 표준화된 `WrappedResponse` 형식으로 감싸는 데 사용됩니다.

## 5. 개발 원칙 준수
-   **객체지향 설계 (OOP)**: `UserRouter`와 `UserService` 모두 클래스 기반으로 구현되어 객체 지향 원칙을 따르며, 각 클래스는 명확한 책임과 메서드를 가집니다.
-   **코드 스타일 (Pythonic Code)**: 코드의 일관성과 가독성을 위해 파이썬 스타일 가이드 및 Ruff 린팅 규칙을 준수합니다.
-   **코드 품질 관리 (Linting)**: `pyproject.toml`에 정의된 Ruff 규칙을 통해 코드 품질이 관리됩니다.
-   **데이터 흐름 (Data Flow)**: Router -> Service 계층의 명확한 분리 및 데이터베이스 쿼리의 외부 파일 관리로 관심사를 분리합니다.
-   **Type Hinting**: 모든 메서드의 인자와 반환 값에 타입 힌트가 명시되어 개발 편의성과 코드 안정성을 높입니다.
