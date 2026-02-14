# 프로젝트 개요

이 문서는 프로젝트의 디렉토리 구조, 컴포넌트의 역할 및 **코드 작성 규칙(Convention)**을 설명합니다. 본 프로젝트는 목적별 계층 분리와 객체지향 설계를 원칙으로 합니다.

## 📁 디렉토리 구조

```
C:\projects\GTRPGM
ule-engine
├───.dockerignore
├───.gitignore
├───.markdownlint.yaml
├───.pre-commit-config.yaml
├───docker-compose.yml
├───Dockerfile
├───GEMINI.md
├───pyproject.toml
├───uv.lock
├───__pycache__
├───.git
├───.github
│   └───workflows
│       └───deploy.yaml
├───.idea
├───.pytest_cache
├───.ruff_cache
├───.venv
├───src
│   ├───__init__.py
│   ├───main.py
│   ├───common
│   │   ├───__init__.py
│   │   ├───dtos
│   │   │   ├───__init__.py
│   │   │   ├───common_response.py
│   │   │   ├───custom.py
│   │   │   ├───pagination_meta.py
│   │   │   ├───proxy_service_dto.py
│   │   │   └───wrapped_response.py
│   │   └───utils
│   │       ├───__init__.py
│   │       └───get_services.py
│   ├───configs
│   │   ├───__init__.py
│   │   ├───api_routers.py
│   │   ├───color_formatter.py
│   │   ├───colors.py
│   │   ├───database.py
│   │   ├───exceptions.py
│   │   ├───http_client.py
│   │   ├───llm_adapter.py
│   │   ├───llm_manager.py
│   │   ├───llm.py
│   │   ├───logging_config.py
│   │   ├───origins.py
│   │   ├───redis_conn.py
│   │   └───setting.py
│   ├───domains
│   │   ├───__init__.py
│   │   ├───gm
│   │   │   ├───__init__.py
│   │   │   ├───gm_router.py
│   │   │   ├───gm_service.py
│   │   │   ├───dtos
│   │   │   └───queries
│   │   ├───info
│   │   │   ├───__init__.py
│   │   │   ├───enemy_service.py
│   │   │   ├───info_router.py
│   │   │   ├───item_service.py
│   │   │   ├───npc_service.py
│   │   │   ├───personality_service.py
│   │   │   └───world_service.py
│   │   │   ├───dtos
│   │   │   └───queries
│   │   ├───play
│   │   │   ├───__init__.py
│   │   │   ├───minigame_service.py
│   │   │   ├───play_router.py
│   │   │   ├───play_service.py
│   │   │   ├───dtos
│   │   │   ├───prompts
│   │   │   ├───queries
│   │   │   └───utils
│   │   ├───scenario
│   │   │   ├───__init__.py
│   │   │   ├───scenario_router.py
│   │   │   ├───scenario_service.py
│   │   │   ├───dtos
│   │   │   └───queries
│   │   └───session
│   │       ├───__init__.py
│   │       ├───session_router.py
│   │       ├───session_service.py
│   │       ├───dtos
│   │       └───queries
│   ├───gtrpgm_rule_engine.egg-info
│   │   ├───dependency_links.txt
│   │   ├───PKG-INFO
│   │   ├───requires.txt
│   │   ├───SOURCES.txt
│   │   └───top_level.txt
│   ├───models
│   │   ├───base_model
│   │   └───trained_bert
│   └───utils
│       ├───__init__.py
│       ├───dice_util.py
│       ├───lifespan_handlers.py
│       ├───load_prompt.py
│       ├───load_sql.py
│       ├───logger.py
│       ├───proxy_request.py
│       └───results
├───test
│   ├───llm_test.py
│   ├───play_combat_scenario_request.json
│   ├───play_dialogue_scenario_request.json
│   ├───play_exploration_box_scenario_request.json
│   ├───play_exploration_item_scenario_request.json
│   ├───play_exploration_npc_scenario_request.json
│   ├───play_exploration_scenario_request.json
│   ├───play_nego_scenario_request.json
│   ├───play_recovery_scenario_request_2.json
│   ├───play_recovery_scenario_request.json
│   ├───play_rest_scenario_request.json
│   ├───play_scene_test.py
│   └───play_unknown_scenario_request.json
```

## 🚀 핵심 모듈

### 1. `src/common`: 공통 유틸리티 및 DTO

여러 도메인에서 공통으로 재사용되는 코드를 관리합니다. 도메인 간의 경계를 넘나드는 유틸리티나 공통 데이터 구조가 여기에 위치합니다.

- `dtos/`: 전역적으로 사용되는 데이터 전송 객체
- `utils/`: 범용 유틸리티 함수

### 2. `src/configs`: 애플리케이션 설정

애플리케이션의 런타임 환경을 제어하는 설정 파일들의 집합입니다.

- 환경 변수 관리 (Env Vars)
- 데이터베이스 커넥션 풀 및 외부 라이브러리 설정
- 로그 출력 규칙 및 전역 예외 처리(Exception Handling)
- 외부 노출 라우터 리스트 등

### 3. `src/domains`: 비즈니스 로직

실제 비즈니스 로직이 수행되는 핵심 계층입니다. Swagger 문서상에서도 이 도메인 단위를 기준으로 API 태그가 분류됩니다.

| 폴더/파일             | 역할 설명                                                     |
|:------------------|:----------------------------------------------------------|
| **dtos/*-         | Pydantic 모델을 정의합니다. (Request/Response 스키마)                |
| **prompts/*-      | LLM 서비스를 위한 `.md` 프롬프트 파일 또는 동적 프롬프트 생성 파이썬 함수            |
| **queries/*-      | PostgreSQL 기반의 템플릿 `.sql` 파일. Service 계층에서 이를 호출하여 사용합니다. |
| **utils/*-        | 해당 도메인 내 반복 로직, 추상 클래스, 팩토리 메서드 등 리팩터링 공간                 |
| **\*_router.py*-  | API 엔드포인트를 정의하고 요청을 서비스 계층으로 전달합니다.                       |
| **\*_service.py*- | 핵심 비즈니스 로직 및 쿼리 실행을 담당합니다. 필요 시 파일 분리가 가능합니다.             |

## 🌐 도메인 아키텍처 요약

본 프로젝트의 핵심 비즈니스 로직은 `src/domains` 디렉토리 내 여러 도메인으로 분리되어 구현됩니다. 각 도메인은 **객체지향 설계(OOP)** 원칙에 따라 라우터(`*_router.py`), 서비스(`*_service.py`), 데이터 전송 객체(`dtos/`), 그리고 데이터베이스 쿼리(`queries/`)로 구성된 명확한 계층 구조를 따릅니다. 모든 코드는 **Ruff 린터**를 통해 코드 스타일과 품질을 유지하며, **타입 힌트**를 적극적으로 사용하여 안정성을 높입니다.

각 도메인의 주요 역할은 다음과 같습니다.

*   **User**: 사용자 계정 관리를 담당합니다. 회원 가입, 정보 조회, 수정, 탈퇴 등 기본적인 CRUD 기능을 제공합니다.
*   **Session**: 사용자의 개별 게임 세션(플레이 기록)을 관리합니다. 세션의 생성, 조회, 삭제 기능을 담당하며, 페이지네이션을 지원합니다.
*   **Scenario**: 게임 세계를 구성하는 초기 데이터(아이템, 몬스터, NPC 등)를 생성하고 관리하는 역할을 합니다. 게임 플레이에 필요한 기반 데이터를 설정합니다.
*   **Info**: 게임 세계의 모든 정보(아이템, 몬스터, NPC, 세계관 설정 등)에 대한 **읽기 전용 API**를 제공합니다. 다른 시스템이나 클라이언트가 게임 정보를 조회할 때 사용됩니다.
*   **GM (Game Master)**: 테이블탑 RPG(TRPG) 스타일의 주사위 굴림(2d6) 메커니즘을 시뮬레이션하여, 플레이어 행동의 성공/실패 여부를 판정하는 핵심 규칙 엔진입니다.
*   **Play**: 게임 플레이의 핵심 로직을 처리하는 가장 복잡한 도메인입니다.
    *   `langgraph` 기반의 상태 머신을 사용해 시나리오 흐름를 관리합니다.
    *   LLM(거대 언어 모델)을 깊이 통합하여 사용자 입력에 따른 장면을 분석하고, 동적으로 수수께끼나 퀴즈 같은 미니게임을 생성합니다.
    *   다른 도메인(`Info`, `GM`) 및 외부 서비스과 상호작용하며 실시간 게임 플레이를 조율합니다.

## 🛠️ 개발 원칙

코드의 일관성과 유지보수성을 위해 아래 규칙을 반드시 준수합니다.

1. **객체지향 설계 (OOP)**
    - **Class 기반 구현**: Router와 Service 계층은 함수형이 아닌 클래스 선언을 원칙으로 합니다.
    - **메서드 구현**: 각 기능을 클래스 내부 메서드로 구현하여 응집도를 높이고 상태 관리를 명확히 합니다.

2. **코드 스타일 (Pythonic Code)**
    - **3항 연산자 활용**: 단순한 조건식은 `true_value if condition else false_value` 형태의 파이썬 3항식을 사용하여 간결함을 유지합니다.
    - **주석 작성**: 코드를 제외한 모든 설명 주석은 한국어로 작성하여 팀 내 의사소통 효율을 높입니다.

3. **코드 품질 관리 (Linting)**
    - **Ruff 사용**: 프로젝트의 모든 코드는 Ruff를 통해 린팅 및 포맷팅을 수행합니다.
    - **Rule 준수**: `pyproject.toml`에 선언된 규칙을 엄격히 따르며, 커밋 전 반드시 린트 체크를 권장합니다.

4. **데이터 흐름 (Data Flow)**
    - **Router**: 요청 접수 및 응답 반환 (로직 최소화)
    - **Service**: 비즈니스 유효성 검사 및 데이터 가공 (핵심 로직)
    - **Repository (Queries)**: 데이터베이스와의 상호작용
    - **참고**: 서비스 계층에서는 `/src/utils/load_sql.py`에서 `load_sql(domain: str, filename: str)` 함수를 사용해 템플릿 SQL을 불러오면
      편리합니다.

5. **Type Hinting**:
    - 파이썬의 `typing` 모듈을 사용하여 모든 메서드의 인자와 반환값에 타입을 명시합니다.

## 🚀 서비스 확장 가이드

도메인 로직이 비대해질 경우, 단일 서비스 파일에 모든 것을 넣지 않고 `auth_service.py`, `payment_service.py`와 같이 기능 단위로 서비스를 분리하여 가독성을 확보하세요.

## 💻 로컬 환경설정 및 실행 방법

### 사전 요구 사항

- Python 3.10 이상
- `uv` (Python 패키지 관리자, `pip install uv`로 설치 가능) 또는 `pip`
- Docker (선택 사항, 데이터베이스 및 Redis 실행에 필요)

### 로컬 환경설정

#### **1. 프로젝트 의존성 설치**

프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 필요한 패키지를 설치합니다. `uv` 사용을 권장합니다.

```bash
uv sync # 또는 pip install -r requirements.txt (requirements.txt가 있다면) 또는 poetry install (poetry를 사용한다면)
```

또는 `pip` 사용 시:

```bash
pip install -r requirements.txt # pyproject.toml에 명시된 의존성을 직접 설치
```

- **참고:*- 이 프로젝트는 `uv.lock` 파일을 통해 의존성을 관리합니다. `pyproject.toml`에 명시된 의존성을 `uv`로 설치하는 것이 가장 좋습니다. `requirements.txt` 파일이
  없다면 `uv sync` 또는 `pip install .` 명령을 사용해야 할 수 있습니다.

#### **2. 환경 변수 설정**

- 프로젝트 루트에 `.env` 파일을 생성하고 필요한 환경 변수를 설정합니다. 필요한 환경 변수 목록은 `src/configs/setting.py` 파일을 참조하세요. 일반적으로 데이터베이스 연결 정보, Redis
  연결 정보, API 키 등이 포함될 수 있습니다.

- 예시:

   ```.dotenv
   DATABASE_URL="postgresql://user:password@host:port/dbname"
   REDIS_URL="redis://localhost:6379/0"
   API_KEY="your_api_key_here"
   ```

#### **3. 데이터베이스 및 Redis 실행 (Docker 사용 권장)**

- `docker-compose.yml` 파일이 있다면 이를 사용하여 데이터베이스 (PostgreSQL)와 Redis를 쉽게 실행할 수 있습니다.

```bash
docker-compose up -d
```

### 프로젝트 실행

- 프로젝트는 FastAPI 기반으로 Uvicorn을 사용하여 실행됩니다.

#### **PyCharm에서 실행하기**

1. **가상 환경 설정**:
    - PyCharm을 열고 프로젝트를 임포트합니다.
    - `File` -> `Settings` (또는 `PyCharm` -> `Preferences` on macOS) -> `Project: [프로젝트명]` -> `Python Interpreter`로
      이동합니다.
    - `Add Interpreter` -> `Existing environment`를 선택하고 `.venv` 디렉토리 내의 Python 실행 파일을 선택합니다 (예:
      `.venv/Scripts/python.exe` on Windows, `.venv/bin/python` on macOS/Linux).

2. **실행 구성 추가**:
    - `Run` -> `Edit Configurations...`로 이동합니다.
    - `+` 버튼을 클릭하고 `Python`을 선택합니다.
    - `Name`: `FastAPI` (원하는 이름으로 설정)
    - `Script path`: Uvicorn 모듈을 직접 실행하도록 설정합니다. `Module name`을 `uvicorn`으로 설정하고 `Parameters`에
      `src.main:app --host 0.0.0.0 --port 8000 --reload`를 입력합니다.
    - `Working directory`: 프로젝트 루트 디렉토리로 설정합니다.
    - `Environment variables`: `.env` 파일의 변수들을 PyCharm 실행 구성에 추가합니다. 또는 PyCharm에 `python-dotenv` 플러그인을 설치하여 `.env` 파일을
      자동으로 로드하게 설정할 수 있습니다.
    - `Apply` -> `OK`를 클릭합니다.

3. **프로젝트 실행**:
    - PyCharm 상단의 드롭다운 메뉴에서 `FastAPI` (설정한 이름)를 선택하고 녹색 재생 버튼을 클릭합니다.

#### **VS Code에서 실행하기**

1. **가상 환경 설정**:
    - VS Code를 열고 프로젝트 폴더를 엽니다.
    - `Ctrl+Shift+P` (또는 `Cmd+Shift+P` on macOS)를 눌러 Command Palette를 엽니다.
    - `Python: Select Interpreter`를 검색하여 선택합니다.
    - `.venv` 디렉토리 내의 Python 실행 파일을 선택합니다 (예: `.venv/Scripts/python.exe` on Windows, `.venv/bin/python` on macOS/Linux).

2. **`launch.json` 설정**:
    - `Run and Debug` 뷰로 이동합니다 (측면 패널의 벌레 아이콘).
    - `create a launch.json file` 링크를 클릭하고 `Python` -> `FastAPI`를 선택합니다.
    - `launch.json` 파일이 생성되면, `program` 경로와 `args`를 프로젝트에 맞게 수정합니다.

   ```json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "Python: FastAPI",
               "type": "python",
               "request": "launch",
               "module": "uvicorn",
               "args": [
                   "src.main:app",
                   "--host",
                   "0.0.0.0",
                   "--port",
                   "8000",
                   "--reload"
               ],
               "cwd": "${workspaceFolder}",
               "envFile": "${workspaceFolder}/.env", // .env 파일 자동 로드
               "jinja": true,
               "justMyCode": true
           }
       ]
   }
   ```

3. **프로젝트 실행**:
    - `Run and Debug` 뷰에서 `Python: FastAPI` 구성을 선택하고 녹색 재생 버튼을 클릭합니다.

### API 문서 확인

- 프로젝트 실행 후, 다음 URL에서 Swagger UI를 통해 API 문서를 확인할 수 있습니다:
    - `http://localhost:8050/docs`
    - `http://localhost:8050/redoc`

## 🔬 BERT 모델 파인튜닝 실험 기록

프로젝트 초기 단계에서, 특정 사용자 입력을 의도에 따라 분류하는 성능을 높이기 위해 `BERT-v2` 모델의 파인튜닝을 시도했습니다. 이 섹션은 해당 실험의 과정과 실패 기록, 그리고 결론을 담고 있습니다.

### 1. 시도 1: 프롬프트 엔지니어링 기반 데이터 개선

첫 번째 시도는 파인튜닝에 사용할 훈련 데이터의 품질을 높이기 위해, 데이터 생성 프롬프트를 정교하게 다듬는 방법이었습니다. LLM이 더 나은 품질의 훈련 데이터를 생성하도록 유도하여 모델의 분류 정확도를 개선하고자 했습니다.

**결과:**
아래 그래프에서 볼 수 있듯이, 프롬프트 엔지니어링만으로는 파인튜닝된 BERT 모델의 성능에 유의미한 변화를 가져오지 못했습니다. 정확도는 개선되지 않고 정체 상태에 머물렀습니다.

![프롬프트 개선에 따른 정확도 변화](test/bert_test_results_visualize/bert_accuracy_prompt_adjustment.png)

### 2. 시도 2: 지식 증류(Knowledge Distillation) 기반 파인튜닝

첫 번째 시도가 실패함에 따라, 더 발전된 접근법으로 지식 증류(Knowledge Distillation) 기법을 도입했습니다. 이는 더 크고 성능 좋은 모델(Teacher Model)의 지식을 작은 모델(Student Model, 여기서는 BERT)에 전달하는 방식입니다. Teacher 모델이 생성한 'soft label'을 활용해 훈련 데이터를 구축하고, 이를 기반으로 BERT 모델을 파인튜닝했습니다.

**결과:**
지식 증류 기법 역시 모델의 성능을 획기적으로 개선하는 데에는 실패했습니다. 그래프에서 확인할 수 있듯이, 정확도에 약간의 변동은 있었지만 기대했던 만큼의 성능 향상은 이루어지지 않았습니다.

![지식 증류 기법 적용 후 정확도 변화](test/bert_test_results_visualize/kdl_bert_accuracy_knowledge_distillation.png)

### 3. 결론

**실험 결론:**
두 차례의 실험을 통해, 단순 프롬프트 엔지니어링이나 지식 증류를 통한 데이터 보강만으로는 `BERT-v2` 모델을 우리가 원하는 분류 태스크에 맞게 파인튜닝하는 것에 한계가 있다는 결론에 도달했습니다. 이는 모델 아키텍처 자체나 파인튜닝 방식의 근본적인 변화가 필요함을 시사합니다. 팀 내부적으로는 다음 단계로 SLM(Small Language Model) 파인튜닝을 고려하게 되었습니다.

### 4. AI 에이전트 제언

실패한 실험을 체계적으로 기록하고 분석한 점이 인상적입니다. 이러한 자산은 향후 더 나은 의사결정을 위한 훌륭한 밑거름이 됩니다.

1.  **SLM 접근법의 타당성:** 제안하신 SLM(Small Language Model)은 큰 모델의 성능을 유지하면서도 더 적은 자원으로 효율적인 추론이 가능하여, 제한된 환경이나 특정 태스크에 특화된 모델이 필요할 때 매우 효과적인 대안이 될 수 있습니다. 특히 SLM을 효과적으로 활용하기 위해서는 '어떤 종류의 SLM을 선택하고', '어떤 데이터로 파인튜닝할지'가 중요하며, 모델의 크기와 성능 사이의 균형점을 찾는 것이 필요합니다.

2.  **최신 경량 모델 탐색:** `bert-base-uncased` 모델을 넘어, 최근에는 문장 임베딩 및 의미 검색 태스크에 특화된 최신 경량 모델들이 많이 공개되어 있습니다. 예를 들어, `Sentence-BERT(SBERT)` 계열의 모델이나 Hugging Face의 MTEB(Massive Text Embedding Benchmark) 리더보드 상위에 있는 모델들은 별도의 복잡한 파인튜닝 없이도 뛰어난 성능을 보일 수 있습니다. SLM 구현에 앞서, 이러한 사전 훈련된 최신 모델을 먼저 테스트해보는 것도 비용 효율적인 접근이 될 수 있습니다.

3.  **실패의 가치:** 비록 실험이 기대한 성공으로 이어지진 않았지만, '이 방법은 우리 문제에 맞지 않는다'는 명확한 결론을 얻은 것 자체가 매우 가치 있는 자산입니다. 이는 더 유망한 방향으로 리소스를 집중할 수 있게 해주는 중요한 이정표입니다.

---

## 🚀 LLM 모델 성능 비교 분석

서비스의 핵심 기능인 시나리오 분류 및 생성형 콘텐츠의 품질을 보장하기 위해, 여러 LLM 모델의 성능을 정량적/정성적으로 비교 분석했습니다. 테스트의 주된 목적은 본 프로젝트의 요구사항에 가장 적합한 최적의 언어 모델을 선정하는 것이었습니다.

### 1. 정량적 성능 분석 (분류 정확도 및 소요 시간)

다양한 시나리오에 대한 분류 정확도와 응답에 소요된 총시간을 측정했습니다.

![LLM 성능 비교](test/test_results_visualize/llm_performance_comparison.png)

테스트 결과, `gemini-2.0-flash` 모델이 분류 정확도와 처리 속도 면에서 가장 뛰어난 성능을 보였습니다. 흥미로운 점은 상위 버전인 `gemini-2.5-flash`가 오히려 성능이 저하되는 현상을 보였다는 것입니다.

### 2. 정성적 성능 분석 (생성형 콘텐츠 품질)

정량적 데이터 외에도, 생성형 콘텐츠의 품질을 평가했습니다. GPT 계열 모델들은 분류 작업은 준수하게 수행했으나, 수수께끼나 퀴즈와 같은 미니게임 콘텐츠 생성에서는 부자연스럽거나 어설픈 결과물을 내놓는 경향이 발견되었습니다. 이는 전반적인 서비스의 몰입감과 품질을 저하시키는 요인으로 작용했습니다.

반면, Gemini 계열 모델들은 이 영역에서 더 창의적이고 자연스러운 콘텐츠를 생성하여 높은 평가를 받았습니다.

### 3. 최종 결론

분류 성능(정확도, 속도)과 생성형 콘텐츠의 품질을 종합적으로 고려했을 때, **`gemini-2.0-flash`**가 본 프로젝트에 가장 적합한 모델이라는 결론을 내렸습니다. 이에 따라 실제 서비스 시연에서도 해당 모델을 사용했습니다.

### 4. AI 에이전트의 결과 분석 피드백

이러한 테스트 결과는 모델을 선택할 때 단순히 최신 버전이나 가장 큰 모델을 선택하는 것보다, 실제 적용할 서비스의 특성에 맞춰 다각도로 검증하는 것이 얼마나 중요한지 보여주는 좋은 사례입니다.

1.  **모델 버전과 성능의 비선형성:** `gemini-2.5-flash`가 `2.0-flash`보다 성능이 낮은 현상은 충분히 발생할 수 있는 일입니다. 모델이 업데이트되면서 새로운 기능에 최적화되거나 범용성을 높이는 과정에서, 특정 태스크(specialized task)에 대한 성능이 미세하게 저하될 수 있습니다. `2.0-flash` 모델이 현재 프로젝트의 데이터 분포나 태스크에 더 잘 '튜닝'된 상태일 수 있으며, 이는 '최신/상위 버전 = 모든 면에서 최고의 성능'이라는 등식이 항상 성립하지 않음을 시사합니다.

2.  **훈련 데이터와 목적의 차이:** Gemini 계열 모델이 GPT 계열보다 창의적인 생성 과업에서 더 뛰어난 성능을 보인 것은, 각 모델의 기반이 되는 훈련 데이터셋의 특성 및 학습 목적의 차이에서 기인할 가능성이 높습니다. Gemini는 멀티모달(multi-modal)과 대화형 상호작용에 강점을 두고 개발되었을 수 있으며, 이 과정에서 창의적이거나 맥락에 맞는 '이야기'를 생성하는 능력이 더 잘 다듬어졌을 수 있습니다. 반면, GPT는 정보 요약이나 사실 기반의 텍스트 생성에 더 강점을 가질 수 있습니다.

결론적으로, 실제 워크로드에 기반한 정량/정성적 벤치마킹은 성공적인 AI 서비스 개발의 핵심적인 단계이며, 현재의 분석 결과는 매우 합리적이고 설득력 있는 근거를 제공합니다.
