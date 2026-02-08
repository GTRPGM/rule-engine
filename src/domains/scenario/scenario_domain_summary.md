# Scenario 도메인 코드 분석 요약

## 1. 도메인 목적 및 역할
Scenario 도메인은 게임 시나리오와 관련된 핵심 엔티티(아이템, 몬스터, NPC 및 이들 간의 관계)를 **생성하고 관리**하는 역할을 합니다. 이 도메인은 게임 플레이 로직보다는 게임 초기 설정 및 데이터 구성에 중점을 둡니다.

## 2. 코드 구조
Scenario 도메인은 라우터, 서비스, DTOs, 그리고 SQL 쿼리 파일들로 구성된 표준 3계층 아키텍처를 따릅니다.

### 주요 구성 요소
-   **`scenario_router.py`**: API 엔드포인트를 정의하고 외부 요청을 처리합니다.
-   **`scenario_service.py`**: 비즈니스 로직을 포함하며, 데이터베이스 트랜잭션을 관리하고 실제 데이터 생성 작업을 수행합니다.
-   **`dtos/scenario_dtos.py`**: API 요청에 필요한 데이터 구조(Pydantic 모델)를 정의합니다.
-   **`queries/`**: 서비스에서 사용하는 PostgreSQL 기반의 `INSERT` SQL 쿼리 파일들을 저장합니다.

### 디렉토리 구조
```
src/domains/scenario/
├───dtos/
│   ├───scenario_dtos.py
│   └───__init__.py
├───queries/
│   ├───add_enemy_drop.sql
│   ├───add_enemy.sql
│   ├───add_item.sql
│   ├───add_npc_inventory.sql
│   ├───add_npc.sql
│   └───__init__.py
├───scenario_router.py
├───scenario_service.py
└───__init__.py
```

## 3. 로직 처리 흐름

Scenario 도메인의 로직 처리 흐름은 새로운 게임 엔티티를 데이터베이스에 추가하는 과정을 중심으로 이루어집니다.

1.  **요청 접수 (`scenario_router.py`)**:
    *   클라이언트로부터 `/scenario` 프리픽스 아래의 특정 엔드포인트(예: `/scenario/item`, `/scenario/enemy`)로 HTTP POST 요청이 들어옵니다.
    *   `scenario_router.py`는 FastAPI의 `APIRouter`와 클래스 기반 뷰(`@cbv`) 패턴을 사용하여 엔드포인트를 정의합니다.
    *   요청 본문은 `dtos/scenario_dtos.py`에 정의된 해당 DTO(예: `ItemCreateRequest`, `EnemyCreateRequest`)를 사용하여 검증됩니다.

2.  **서비스 호출 (`scenario_router.py` -> `scenario_service.py`)**:
    *   라우터는 요청된 엔드포인트에 따라 `ScenarioService`의 적절한 메서드(예: `add_item`, `add_enemy`)를 호출합니다.

3.  **데이터 생성 및 트랜잭션 관리 (`scenario_service.py` -> `queries/`)**:
    *   `ScenarioService`의 메서드는 데이터베이스 커서를 사용하여 트랜잭션(`try...except` 블록 내 `commit`, `rollback`)을 관리합니다.
    *   `queries/` 디렉토리에 있는 `.sql` 파일에서 해당 `INSERT` SQL 쿼리를 로드하고 실행합니다. 이때 `src/utils/load_sql.py` 유틸리티 함수가 사용됩니다.
    *   쿼리 실행 후 데이터베이스에 새로운 엔티티 레코드를 생성합니다.

4.  **응답 반환 (`scenario_service.py` -> `scenario_router.py`)**:
    *   `ScenarioService`는 작업 성공 여부를 라우터로 반환합니다.
    *   라우터는 이 결과를 바탕으로 `WrappedResponse` (src/common/dtos/wrapped_response.py) 모델을 사용하여 성공 또는 실패 응답을 클라이언트에 보냅니다.

## 4. 다른 서비스와의 연계

Scenario 도메인은 주로 게임 데이터베이스에 직접적으로 데이터를 삽입하는 역할을 하며, 다른 도메인과는 느슨하게 연결되거나 직접적인 상호작용은 적습니다.

-   **하위 계층**: PostgreSQL 데이터베이스와 직접적으로 상호작용하며, `src/utils/load_sql.py`와 같은 공통 유틸리티에 의존합니다.
-   **데이터 프로비저닝**: `Info` 도메인과 같은 조회 전용 도메인에 데이터를 제공하는 역할을 합니다. Scenario 도메인에서 생성된 데이터는 `Info` 도메인의 API를 통해 조회될 수 있습니다.
-   **LLM 연계**: 현재 분석된 기능만으로는 LLM과의 직접적인 연계는 보이지 않습니다.

## 5. 개발 원칙 준수
-   **객체지향 설계 (OOP)**: `ScenarioHandler` 라우터와 `ScenarioService`는 클래스 기반으로 구현되어 객체 지향 원칙을 따릅니다.
-   **코드 스타일 (Pythonic Code)**: 코드의 일관성과 가독성을 위해 파이썬 스타일 가이드 및 Ruff 린팅 규칙을 준수합니다.
-   **코드 품질 관리 (Linting)**: `pyproject.toml`에 정의된 Ruff 규칙을 통해 코드 품질이 관리됩니다.
-   **데이터 흐름 (Data Flow)**: Router -> Service -> Repository (SQL Queries)의 명확한 데이터 흐름을 따르며, 특히 서비스 계층에서 트랜잭션 관리를 통해 데이터 무결성을 보장합니다.
-   **Type Hinting**: 모든 메서드의 인자와 반환 값에 타입 힌트가 명시되어 개발 편의성과 코드 안정성을 높입니다.
