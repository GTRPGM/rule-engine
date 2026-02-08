# Play 도메인 코드 분석 요약

## 1. 도메인 목적 및 역할
Play 도메인은 게임 플레이의 핵심 로직을 담당하며, 사용자 액션에 대한 시나리오 처리, 미니게임(수수께끼, 퀴즈) 생성 및 검증, 플레이어 상태 조회 등을 제공합니다. 특히 **LLM (Large Language Model)을 깊이 있게 통합**하여 동적이고 유연한 게임 콘텐츠 생성 및 상황 분석을 수행합니다.

## 2. 코드 구조
Play 도메인은 크게 라우터, 두 가지 주요 서비스, DTOs, 프롬프트, 그리고 유틸리티 모듈로 구성됩니다.

### 주요 구성 요소
-   **`play_router.py`**: 게임 플레이 관련 모든 API 엔드포인트를 정의하고, 클라이언트 요청을 `PlayService` 또는 `MinigameService`로 라우팅합니다.
-   **`play_service.py`**: `langgraph` 기반의 상태 머신을 활용하여 복잡한 게임 시나리오의 흐름을 조율하고, LLM을 통해 상황을 분석하여 적절한 게임 페이즈(전투, 탐험, 대화 등) 로직을 실행합니다.
-   **`minigame_service.py`**: 수수께끼 및 퀴즈와 같은 미니게임을 생성하고, 사용자 답변을 검증하는 로직을 담당합니다. LLM을 사용하여 문제와 답을 동적으로 생성하며, Redis를 통해 미니게임 상태를 관리합니다.
-   **`dtos/`**: `PlaySceneRequest`, `PlaySceneResponse`, `FullPlayerState`, `AnswerRequest`, `RiddleData` 등 Pydantic 모델을 정의하여 API 요청 및 응답 데이터, 그리고 LLM과의 구조화된 데이터 교환 형식을 정의합니다.
-   **`prompts/`**: LLM이 특정 작업을 수행하도록 안내하는 `.md` 파일 형식의 시스템 프롬프트(예: `riddle_system_prompt.md`) 및 동적으로 프롬프트를 생성하는 파이썬 함수(예: `generate_riddle_prompt`, `generate_quiz_prompt`, `answer_validation_prompt`)를 포함합니다.
-   **`utils/`**:
    *   **`nodes.py`**: `play_service.py`의 `langgraph` 워크플로에서 사용되는 일반 노드(장면 분석, 세계 데이터 가져오기, 엔티티 분류 등)를 정의합니다.
    *   **`phase_nodes/`**: 각 게임 페이즈(combat, exploration, dialogue, nego, rest, recovery, unknown)별 구체적인 로직을 캡슐화하는 노드들을 정의합니다.

### 디렉토리 구조
```
src/domains/play/
├───dtos/
│   ├───play_dtos.py
│   ├───player_dtos.py
│   ├───riddle_dtos.py
│   └───__init__.py
├───prompts/
│   ├───answer_validation_prompt.py
│   ├───instruction.md
│   ├───potion_selection_prompt.py
│   ├───prob_generator_prompt.py
│   ├───riddle_generator_prompt.py
│   ├───riddle_system_prompt.md
│   └───__init__.py
├───queries/
│   └───__init__.py
├───utils/
│   ├───dummy_player.py
│   ├───nodes.py
│   ├───__init__.py
│   └───phase_nodes/
│       ├───combat_node.py
│       ├───dialogue_node.py
│       ├───exploration_node.py
│       ├───nego_node.py
│       ├───recovery_node.py
│       ├───rest_node.py
│       ├───unknown_node.py
│       └───__init__.py
├───minigame_service.py
├───play_router.py
├───play_service.py
└───__init__.py
```

## 3. 로직 처리 흐름

### `play_router.py` (API 엔드포인트)
-   **`POST /play/scenario`**: 플레이어의 시나리오 요청(`PlaySceneRequest`)을 받아 `PlayService.play_scene` 메서드를 호출하여 처리합니다. 처리 결과를 `PlaySceneResponse`로 반환합니다.
-   **`GET /play/player/{player_id}`**: 특정 플레이어의 상세 정보를 조회합니다. 이 요청은 `proxy_request` 유틸리티를 통해 외부 `STATE_MANAGER` 서비스로 전달되어 처리됩니다.
-   **`GET /play/riddle/{user_id}`**: `MinigameService.generate_and_save_riddle`을 호출하여 새로운 수수께끼를 생성하고, 이를 스트리밍 방식으로 클라이언트에 전송합니다. 생성된 수수께끼의 정답과 상태는 Redis에 저장됩니다.
-   **`GET /play/quiz/{user_id}`**: `MinigameService.generate_and_save_quiz`를 호출하여 새로운 퀴즈를 생성하고 스트리밍으로 전송합니다. 이 과정에서 `Info` 도메인의 여러 서비스(ItemService, EnemyService 등)를 주입받아 퀴즈 생성에 활용합니다. 정답과 상태는 Redis에 저장됩니다.
-   **`POST /play/answer/{user_id}`**: 사용자가 미니게임(`riddle` 또는 `quiz`)에 대한 답변을 제출하면 `MinigameService.check_user_answer`를 호출하여 정답 여부를 확인합니다. 3회 오답 시 힌트를 제공하며, 남은 시간(TTL) 정보도 함께 반환합니다.

### `play_service.py` (시나리오 처리)
1.  **초기화**: `LLMManager`로부터 LLM 인스턴스를 가져오고, `structured_output` 기능을 사용하여 `SceneAnalysis` DTO 형식으로 분석 결과를 반환하는 `analyzer`를 준비합니다. `GmService`, `WorldService`, `ItemService`, `EnemyService` 등 관련 서비스 인스턴스도 초기화합니다.
2.  **`langgraph` 워크플로 구축**:
    *   `PlaySessionState`를 상태 객체로 하는 `StateGraph`를 정의합니다.
    *   **노드 추가**: `analyze_scene_node`, `fetch_world_data_node`, `categorize_entities_node`와 같은 일반 처리 노드 및 `combat_node`, `exploration_node`, `dialogue_node` 등 다양한 게임 페이즈별 노드를 등록합니다.
    *   **엣지 연결**: `analyze_scene` -> `fetch_world_data` -> `categorize_entities` 순서로 기본 흐름을 연결합니다.
    *   **조건부 엣지**: `categorize_entities` 노드 이후, `_route_phase` 메서드를 통해 `PlaySessionState` 내 `analysis.phase_type` 값에 따라 실제 게임 페이즈 노드(예: `combat`, `exploration`) 중 하나로 동적으로 라우팅됩니다. 각 페이즈 노드는 `END`로 끝납니다.
3.  **`play_scene` 실행**: `play_router`로부터 `PlaySceneRequest`를 받으면, 초기 `PlaySessionState`를 구성하고 `self.graph.ainvoke(initial_state)`를 통해 `langgraph` 워크플로를 비동기적으로 실행합니다. 워크플로의 최종 상태를 기반으로 `PlaySceneResponse`를 생성하여 반환합니다.

### `minigame_service.py` (미니게임 처리)
1.  **초기화**: Redis 클라이언트를 설정하고, 문제 생성을 위한 LLM(`examiner`, 높은 온도)과 정답 검증을 위한 LLM(`evaluator`, 낮은 온도)을 각각 초기화합니다. 수수께끼 및 퀴즈 테마 목록을 정의합니다.
2.  **수수께끼 생성 (`generate_and_save_riddle`)**:
    *   `examiner` LLM을 사용하여 무작위 테마의 수수께끼, 정답, 힌트, 설명을 `RiddleData` DTO 형식으로 생성합니다.
    *   생성된 데이터를 `fail_count` 및 `total_time_limit`와 함께 Redis에 저장하고 15분 TTL을 설정합니다.
    *   수수께끼 텍스트를 문자 단위로 스트리밍하는 제너레이터를 반환합니다.
3.  **퀴즈 생성 (`generate_and_save_quiz`)**:
    *   무작위 테마를 선택하고, 해당 테마에 맞는 `Info` 도메인 서비스(예: `item_service`)로부터 관련 정보를 동적으로 조회합니다.
    *   `examiner` LLM을 사용하여 조회된 정보를 기반으로 퀴즈를 `RiddleData` DTO 형식으로 생성합니다.
    *   생성된 데이터를 Redis에 저장하고 15분 TTL을 설정합니다.
    *   퀴즈 텍스트를 문자 단위로 스트리밍하는 제너레이터를 반환합니다.
4.  **정답 검증 (`check_user_answer`)**:
    *   Redis에서 해당 미니게임의 저장된 데이터를 가져오고, 남은 시간(TTL)을 확인합니다.
    *   `validate_with_llm` 메서드를 호출하여 사용자 답변의 정확성을 확인합니다.
    *   정답인 경우 Redis 데이터를 삭제하고 성공 응답을 반환합니다. 오답인 경우 `fail_count`를 증가시키고, 3회 이상 오답 시 힌트를 포함한 피드백을 제공하며, Redis 데이터를 업데이트합니다(TTL 유지).
5.  **LLM을 통한 정답 검증 (`validate_with_llm`)**:
    *   먼저 사용자 답변과 정답을 소문자 및 공백 제거 후 직접 비교합니다.
    *   일치하지 않으면 `evaluator` LLM을 사용하여 `answer_validation_prompt`에 따라 의미론적 검증을 수행하고, LLM 응답에 "Y"가 포함되어 있는지 여부로 정답을 판정합니다.

## 4. 다른 서비스와의 연계

Play 도메인은 여러 외부 및 내부 서비스와 긴밀하게 연동됩니다.

-   **LLM (Large Language Model)**: `LLMManager`를 통해 관리되는 LLM은 시나리오 분석(`play_service`), 미니게임 생성(`minigame_service`), 그리고 사용자 답변의 의미론적 검증(`minigame_service`) 등 핵심적인 역할을 수행합니다. `prompts/` 디렉토리의 프롬프트들을 통해 LLM의 행동을 제어합니다.
-   **Redis**: `minigame_service`에서 미니게임의 실시간 상태(정답, 힌트, 오답 횟수, 제한 시간)를 저장하고 관리하는 데 필수적으로 사용됩니다.
-   **`STATE_MANAGER` (외부 서비스)**: `play_router`의 `GET /play/player/{player_id}` 엔드포인트에서 플레이어의 상세 상태 정보를 조회하기 위해 `proxy_request`를 통해 호출됩니다.
-   **Info 도메인 서비스**: `minigame_service`의 퀴즈 생성 로직에서 `ItemService`, `EnemyService`, `NpcService`, `PersonalityService`, `WorldService` 등의 서비스를 동적으로 활용하여 게임 세계의 실제 데이터에 기반한 컨텍스트가 풍부한 퀴즈를 생성합니다.
-   **GM 도메인 서비스 (`GmService`)**: `play_service`의 `langgraph` 워크플로 내에서 필요에 따라 주사위 판정 로직을 위해 호출될 수 있습니다.
-   **`src/utils` 유틸리티**:
    *   `load_prompt.py`: `prompts/` 디렉토리의 프롬프트 파일들을 로드합니다.
    *   `proxy_request.py`: 외부 서비스로의 요청을 처리합니다.
    *   `logger.py`: 로그를 기록합니다.

## 5. 개발 원칙 준수
-   **객체지향 설계 (OOP)**: `PlayRouter`, `PlayService`, `MinigameService` 모두 클래스 기반으로 구현되어 객체 지향 원칙을 따르며, 각 클래스는 명확한 책임과 메서드를 가집니다.
-   **코드 스타일 (Pythonic Code)**: 코드의 일관성과 가독성을 위해 파이썬 스타일 가이드 및 Ruff 린팅 규칙을 준수합니다.
-   **코드 품질 관리 (Linting)**: `pyproject.toml`에 정의된 Ruff 규칙을 통해 코드 품질이 관리됩니다.
-   **데이터 흐름 (Data Flow)**: Router -> Service 계층의 명확한 분리 및 `langgraph`를 통한 복잡한 비즈니스 로직의 체계적 관리. LLM과의 상호작용은 구조화된 DTO를 통해 이루어집니다.
-   **Type Hinting**: 모든 메서드의 인자와 반환 값에 타입 힌트가 명시되어 개발 편의성과 코드 안정성을 높입니다.
