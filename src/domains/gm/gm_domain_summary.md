# GM (Game Master) 도메인 코드 분석 요약

## 1. 도메인 목적 및 역할
GM (Game Master) 도메인은 게임 내 핵심 메커니즘 중 하나인 **주사위 기반 성공 여부 판정**을 담당합니다. 이는 테이블탑 RPG(TRPG) 스타일의 주사위 굴림을 시뮬레이션하여 플레이어의 행동 결과(성공, 실패, 치명적 성공/실패)를 결정하는 역할을 합니다.

## 2. 코드 구조
GM 도메인은 다음과 같은 주요 파일들로 구성됩니다.

-   **`gm_router.py`**: API 엔드포인트를 정의하고 외부 요청을 처리합니다.
-   **`gm_service.py`**: 비즈니스 로직을 포함하며, 주사위 판정의 핵심 과정을 조율합니다.
-   **`dtos/dice_check_result.py`**: 주사위 판정 결과 데이터를 위한 DTO(Data Transfer Object)를 정의합니다.

### 디렉토리 구조
```
src/domains/gm/
├───dtos/
│   ├───dice_check_result.py
│   └───__init__.py
├───gm_router.py
├───gm_service.py
└───__init__.py
```

## 3. 로직 처리 흐름
GM 도메인의 주사위 판정 로직은 다음과 같은 단계로 처리됩니다.

1.  **요청 접수 (`gm_router.py`)**:
    *   `gm_router.py`에 정의된 `/gm/action/check` 엔드포인트로 HTTP GET 요청이 들어옵니다.
    *   이때 플레이어의 `ability_val` (능력치)과 `diff` (난이도)가 쿼리 파라미터로 전달됩니다.
    *   (코드 주석에 따르면, 이 엔드포인트는 백업 또는 디버깅 용도로, 주요 애플리케이션 흐름의 일부는 아닐 수 있습니다.)

2.  **서비스 호출 (`gm_router.py` -> `gm_service.py`)**:
    *   라우터는 `GmService` 클래스의 `rolling_dice` 메서드를 호출하여 실제 비즈니스 로직 처리를 위임합니다.

3.  **주사위 판정 로직 (`gm_service.py` -> `src/utils/dice_util.py`)**:
    *   `GmService`는 핵심 주사위 계산 로직을 `src/utils/dice_util.py` 파일 내 `DiceUtil.check_success` 유틸리티 메서드에 위임합니다.
    *   `DiceUtil`은 2d6 (주사위 두 개를 굴려 합산) 굴림을 시뮬레이션하고, 여기에 `ability_score`를 더합니다.
    *   최종 합산 결과와 `difficulty`를 비교하여 성공/실패를 판정합니다.
    *   또한, 주사위 굴림 결과가 12일 경우 '치명적 성공', 2일 경우 '치명적 실패'를 특별히 처리합니다.

4.  **결과 처리 및 반환 (`gm_service.py` -> `gm_router.py`)**:
    *   `GmService`는 `DiceUtil`로부터 받은 상세 결과를 바탕으로 "성공!", "치명적 실패..."와 같은 사용자 친화적인 메시지를 구성합니다.
    *   이 모든 정보를 `dtos/dice_check_result.py`에 정의된 `DiceCheckResult` DTO 객체에 담아 반환합니다.

5.  **응답 생성 (`gm_router.py`)**:
    *   라우터는 `DiceCheckResult` DTO를 JSON 형태로 직렬화하여 클라이언트에 응답합니다.

## 4. 다른 서비스와의 연계
GM 도메인은 현재 분석된 기능 상으로는 다른 도메인과 직접적인 상호작용이나 LLM(Large Language Model) 의존성을 가지지 않습니다. 'GM'이라는 이름은 규칙의 중립적인 중재자로서의 기능(테이블탑 RPG의 게임 마스터처럼)을 의미하며, 다른 시스템의 구성 요소가 필요할 때 이 주사위 판정 유틸리티를 호출할 수 있도록 제공하는 역할을 합니다.

-   **의존성**: `gm_service`는 `src/utils/dice_util.py`의 `DiceUtil`에만 의존합니다. `GmService`는 데이터베이스 커서로 초기화되지만, 현재 분석된 주사위 판정 기능에서는 데이터베이스를 사용하지 않습니다. 이는 서비스가 다른 숨겨진 기능들을 가지고 있거나, 향후 확장을 위해 미리 준비된 것일 수 있습니다.

## 5. 개발 원칙 준수
-   **OOP**: `GmRouter`와 `GmService` 모두 클래스 기반으로 구현되어 객체 지향 설계를 따릅니다.
-   **Type Hinting**: 모든 메서드의 인자와 반환 값에 타입 힌트가 명시되어 코드의 가독성과 안정성을 높입니다.
-   **데이터 흐름**: Router는 요청/응답을, Service는 비즈니스 로직을, Util은 핵심 계산을 담당하여 역할이 명확히 분리되어 있습니다.