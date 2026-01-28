# 🏗️ Project Architecture: GEMINI

이 문서는 프로젝트의 디렉토리 구조, 컴포넌트의 역할 및 **코드 작성 규칙(Convention)**을 설명합니다. 본 프로젝트는 목적별 계층 분리와 객체지향 설계를 원칙으로 합니다.

## 📁 Directory Structure

```angular2html
├─gitub
│  └─workflows   # 깃허브 액션
├─.venv          # uv 가상환경
├─src
│  ├─common      # 공통 유틸리티 및 DTO (도메인 간 공유)
│  ├─configs     # 시스템 설정 및 인프라스트럭처 설정
│  └─domains     # 실제 서비스 로직 (도메인별 격리)
│      ├─gm
│      ├─info
│      ├─play
│      └─scenario
├─test           # 단위 및 통합 테스트 코드
└─pyproject.toml     # Ruff 린트 및 프로젝트 의존성 설정
└─...
```

---

## 🚀 Core Modules

1. src/common: 여러 도메인에서 공통으로 재사용되는 코드를 관리합니다. 도메인 간의 경계를 넘나드는 유틸리티나 공통 데이터 구조가 여기에 위치합니다.

    - dtos/: 전역적으로 사용되는 데이터 전송 객체
    - utils/: 범용 유틸리티 함수

2. src/configs: 애플리케이션의 런타임 환경을 제어하는 설정 파일들의 집합입니다.

- 환경 변수 관리 (Env Vars)
- 데이터베이스 커넥션 풀 및 외부 라이브러리 설정
- 로그 출력 규칙 및 전역 예외 처리(Exception Handling)
- 외부 노출 라우터 리스트 등

3. src/domains: 실제 비즈니스 로직이 수행되는 핵심 계층입니다. Swagger 문서상에서도 이 도메인 단위를 기준으로 API 태그가 분류됩니다.

   | 폴더/파일             | 역할 설명                                                   |
      |:------------------|:--------------------------------------------------------|
   | **dtos/**         | Pydantic 모델을 정의합니다. (Request/Response 스키마)              |
   | **prompts/**      | LLM 서비스를 위한 .md 프롬프트 파일 또는 동적 프롬프트 생성 파이썬 함수            |
   | **queries/**      | PostgreSQL 기반의 템플릿 .sql 파일. Service 계층에서 이를 호출하여 사용합니다. |
   | **utils/**        | 해당 도메인 내 반복 로직, 추상 클래스, 팩토리 메서드 등 리팩터링 공간               |
   | **\*_router.py**  | API 엔드포인트를 정의하고 요청을 서비스 계층으로 전달합니다.                     |
   | **\*_service.py** | 핵심 비즈니스 로직 및 쿼리 실행을 담당합니다. 필요 시 파일 분리가 가능합니다.           |

---

## 🛠️ Development Principles

🛠️ Development Principles & Rules
코드의 일관성과 유지보수성을 위해 아래 규칙을 반드시 준수합니다.

1. 객체지향 설계 (OOP)

- Class 기반 구현: Router와 Service 계층은 함수형이 아닌 클래스 선언을 원칙으로 합니다.
- 메서드 구현: 각 기능을 클래스 내부 메서드로 구현하여 응집도를 높이고 상태 관리를 명확히 합니다.

2. 코드 스타일 (Pythonic Code)

- 3항 연산자 활용: 단순한 조건식은 true_value if condition else false_value 형태의 파이썬 3항식을 사용하여 간결함을 유지합니다.
- 주석 작성: 코드를 제외한 모든 설명 주석은 한국어로 작성하여 팀 내 의사소통 효율을 높입니다.

3. 코드 품질 관리 (Linting)

- Ruff 사용: 프로젝트의 모든 코드는 Ruff를 통해 린팅 및 포맷팅을 수행합니다.
- Rule 준수: pyproject.toml에 선언된 규칙을 엄격히 따르며, 커밋 전 반드시 린트 체크를 권장합니다.

4. 데이터 흐름 (Data Flow)

- Router: 요청 접수 및 응답 반환 (로직 최소화)
- Service: 비즈니스 유효성 검사 및 데이터 가공 (핵심 로직)
- Repository (Queries): 데이터베이스와의 상호작용
- 참고
    - 서비스 계층에서는 /src/utils/load_sql.py에서 load_sql(domain: str, filename: str) 함수를 사용해 템플릿 SQL을 불러오면 편리합니다.

5. Type Hinting:

- 파이썬의 typing 모듈을 사용하여 모든 메서드의 인자와 반환값에 타입을 명시합니다.

6. Gemini 협업 및 응답 규칙

- 언어 설정: 제미나이(AI)와의 모든 대화 및 제미나이의 모든 응답은 한국어로 진행합니다.
- 코드 가이드: 제미나이는 코드를 제안할 때 본 문서에 명시된 OOP 구조와 Ruff 스타일을 반영해야 합니다.

---

## 💡 Tip: 서비스 확장 가이드

도메인 로직이 비대해질 경우, 단일 서비스 파일에 모든 것을 넣지 않고 auth_service.py, payment_service.py와 같이 기능 단위로 서비스를 분리하여 가독성을 확보하세요.
