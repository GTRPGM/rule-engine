# Info 도메인 코드 분석 요약

## 1. 도메인 목적 및 역할
Info 도메인은 게임 세계의 다양한 정보(아이템, 몬스터, NPC, 세계관 설정 등)를 조회할 수 있는 **읽기 전용 API**를 제공합니다. 이는 게임 내 정보 검색 기능을 담당하며, 표준 계층형 아키텍처를 따릅니다.

## 2. 코드 구조
Info 도메인은 `info_router.py`와 여러 개의 서비스 파일(`*_service.py`), DTOs, 그리고 SQL 쿼리 파일들로 구성됩니다.

### 주요 구성 요소
-   **`info_router.py`**: 모든 API 엔드포인트를 정의하고, 요청을 각 서비스로 라우팅하는 역할을 합니다.
-   **`*_service.py` (예: `enemy_service.py`, `item_service.py`, `npc_service.py`, `personality_service.py`, `world_service.py`)**: 각 서비스는 특정 정보 유형(예: 아이템, 몬스터)에 대한 비즈니스 로직을 캡슐화합니다. 데이터베이스에서 데이터를 조회하고, 필요한 경우 페이지네이션 메타데이터를 계산합니다.
-   **`dtos/`**: Pydantic 모델을 사용하여 API 요청 및 응답 데이터의 형식을 정의합니다. 이는 타입 안정성과 데이터 유효성 검사를 보장합니다.
-   **`queries/`**: 서비스에서 사용하는 PostgreSQL 기반의 템플릿 SQL 쿼리 파일들을 저장합니다. `load_sql` 유틸리티를 사용하여 서비스에서 동적으로 로드됩니다.

### 디렉토리 구조
```
src/domains/info/
├───dtos/
│   ├───enemy_dtos.py
│   ├───item_dtos.py
│   ├───npc_dtos.py
│   ├───personality_dtos.py
│   ├───world_dtos.py
│   └───__init__.py
├───queries/
│   ├───count_enemies.sql
│   ├───count_items.sql
│   ├───count_npcs.sql
│   ├───count_personalities.sql
│   ├───get_abilities.sql
│   ├───get_characters.sql
│   ├───get_enemies.sql
│   ├───get_enemy_detail.sql
│   ├───get_items.sql
│   ├───get_npc.sql
│   ├───get_npcs.sql
│   ├───get_personalities.sql
│   ├───get_sys_configs.sql
│   ├───get_world_eras.sql
│   ├───get_world_locales.sql
│   └───__init__.py
├───enemy_service.py
├───info_router.py
├───item_service.py
├───npc_service.py
├───personality_service.py
├───world_service.py
└───__init__.py
```

## 3. 로직 처리 흐름

Info 도메인의 로직 처리 흐름은 일반적인 웹 API 요청 처리 패턴을 따릅니다.

1.  **요청 접수 (`info_router.py`)**:
    *   클라이언트로부터 `/info` 프리픽스 아래의 특정 엔드포인트(예: `/info/items`, `/info/enemies`)로 HTTP 요청이 들어옵니다.
    *   `info_router.py`는 FastAPI의 `APIRouter`와 클래스 기반 뷰(`@cbv`) 패턴을 사용하여 엔드포인트를 정의합니다.
    *   요청 처리 시 필요한 서비스 인스턴스는 FastAPI의 의존성 주입(`Depends`)을 통해 라우터 핸들러에 전달됩니다.

2.  **서비스 호출 (`info_router.py` -> `*_service.py`)**:
    *   라우터는 요청된 엔드포인트에 따라 해당 서비스(예: `ItemService`, `EnemyService`)의 적절한 메서드를 호출합니다.

3.  **데이터 조회 및 처리 (`*_service.py` -> `queries/`)**:
    *   각 서비스 메서드는 데이터베이스 커서를 사용하여 `queries/` 디렉토리에 있는 `.sql` 파일에서 SQL 쿼리를 로드하고 실행합니다. 이때 `src/utils/load_sql.py`의 `load_sql` 유틸리티 함수가 사용됩니다.
    *   대부분의 정보 조회 서비스는 페이지네이션을 지원하기 위해 두 가지 유형의 쿼리를 사용합니다:
        *   총 개수를 세는 쿼리 (예: `count_items.sql`)
        *   현재 페이지에 해당하는 데이터를 가져오는 쿼리 (예: `get_items.sql`)
    *   서비스는 SQL 쿼리 결과를 받아 가공하고, 필요한 경우 페이지네이션 메타데이터를 계산하여 반환합니다.

4.  **응답 데이터 구성 및 반환 (`*_service.py` -> `info_router.py`)**:
    *   서비스는 조회된 데이터를 `dtos/`에 정의된 적절한 DTO(예: `ItemResponseDTO`, `EnemyListResponseDTO`) 형태로 패키징하여 라우터로 전달합니다.
    *   라우터는 이 DTO 객체를 `WrappedResponse` (src/common/dtos/wrapped_response.py) 모델로 감싸 최종 JSON 응답을 클라이언트에 보냅니다.

## 4. 다른 서비스와의 연계

Info 도메인은 주로 다른 시스템 컴포넌트나 클라이언트에게 정보를 제공하는 역할을 합니다.

-   **상위 계층**: 웹 프론트엔드 또는 다른 마이크로서비스에서 게임 정보를 조회하기 위해 Info 도메인의 API를 호출할 수 있습니다.
-   **하위 계층**: PostgreSQL 데이터베이스와 직접적으로 상호작용하며, `src/utils/load_sql.py`와 같은 공통 유틸리티에 의존합니다.
-   **LLM 연계**: 현재 분석된 기능만으로는 LLM과의 직접적인 연계는 보이지 않습니다. (명시적인 `prompts/` 디렉토리가 없으며, `llm_manager` 등의 사용 흔적도 없음)
-   **특징**: 각 정보 서비스는 다른 정보 서비스와 직접적으로 강하게 결합되어 있지 않으며, 독립적으로 데이터를 조회하고 처리하는 경향이 있습니다. 이는 모듈성을 높이고 각 서비스의 책임 범위를 명확히 합니다.

## 5. 개발 원칙 준수
-   **객체지향 설계 (OOP)**: `InfoHandler` 라우터와 모든 서비스(`*_service.py`)는 클래스 기반으로 구현되어 객체 지향 원칙을 따릅니다. 각 클래스는 명확한 책임과 메서드를 가집니다.
-   **코드 스타일 (Pythonic Code)**: 코드의 일관성과 가독성을 위해 파이썬 스타일 가이드와 Ruff 린팅 규칙을 준수합니다.
-   **코드 품질 관리 (Linting)**: `pyproject.toml`에 정의된 Ruff 규칙을 통해 코드 품질이 관리됩니다.
-   **데이터 흐름 (Data Flow)**: Router -> Service -> Repository (SQL Queries)의 명확한 데이터 흐름을 따릅니다.
-   **Type Hinting**: 모든 메서드의 인자와 반환 값에 타입 힌트가 명시되어 개발 편의성과 코드 안정성을 높입니다.