import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from domains.play.dtos.play_dtos import PhaseType, PlaySceneRequest
from domains.play.play_service import PlayService


def load_stories_from_json(file_path: str | Path) -> list[tuple[PhaseType, str]]:
    """
    JSON 파일에서 테스트 케이스를 로드합니다.

    Args:
        file_path: sample_stories.json 파일 경로

    Returns:
        (PhaseType, story) 튜플의 리스트
    """
    phase_type_mapping = {
        "탐험": PhaseType.EXPLORATION,
        "전투": PhaseType.COMBAT,
        "대화": PhaseType.DIALOGUE,
        "흥정": PhaseType.NEGO,
        "휴식": PhaseType.REST,
        "회복": PhaseType.RECOVERY,
        "알 수 없음": PhaseType.UNKNOWN,
    }

    stories = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            phase_type_str = item.get("phase_type")
            story = item.get("story")
            if phase_type_str and story:
                phase_type = phase_type_mapping.get(phase_type_str)
                if phase_type:
                    stories.append((phase_type, story))
    except FileNotFoundError:
        pytest.fail(f"테스트 데이터 파일을 찾을 수 없습니다: {file_path}")
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"테스트 데이터 파일 파싱 중 오류 발생: {e}")

    return stories


@pytest.fixture
def service():
    """PlayService 인스턴스를 생성하는 pytest fixture"""
    mock_cursor = MagicMock()
    return PlayService(cursor=mock_cursor, llm_provider="gateway")


@pytest.mark.asyncio
async def test_play_scene_analysis(service: PlayService, capsys):
    """
    play_scene 메서드를 통해 LLM의 장면 분석 성능 및 정확도를 테스트합니다.
    테스트 데이터는 sample_stories.json 파일에서 로드합니다.
    """
    log_dir = Path("test/bert_test_logs")
    log_dir.mkdir(exist_ok=True)
    sample_stories = load_stories_from_json(
        Path("test/sample_stories/sample_stories.json")
    )

    if not sample_stories:
        pytest.skip("로드된 테스트 스토리가 없어 테스트를 건너뜁니다.")

    print(f"\n{'=' * 60}\n LLM 성능 및 정확도 테스트 시작 (총 {len(sample_stories)}개 케이스)\n{'=' * 60}")

    test_results = []
    correct_count = 0
    total_start_time = time.perf_counter()

    for i, (expected_type, story) in enumerate(sample_stories):
        start_time = time.perf_counter()

        request = PlaySceneRequest(
            session_id=f"test_session_{i}",
            scenario_id="test_scenario",
            locale_id=1,
            entities=[],
            relations=[],
            story=story,
        )

        response = await service.play_scene(request)
        elapsed = time.perf_counter() - start_time

        is_correct = response.phase_type == expected_type
        if is_correct:
            correct_count += 1

        case_result = {
            "story": story,
            "expected": expected_type.name,
            "actual": response.phase_type.name,
            "is_correct": is_correct,
            "confidence": 0.0,
            "reason": response.reason,
            "elapsed": round(elapsed, 3),
        }
        test_results.append(case_result)

        with capsys.disabled():
            print(f"\n[입력 {i + 1}/{len(sample_stories)}]: {story[:70]}...")
            print(
                f"[결과] 정답: {expected_type.name} |"
                f" 예상: {response.phase_type.name} ({'PASS' if is_correct else 'FAIL'})"
            )
            print(f"소요시간: {elapsed:.2f}초")
            print(f"{'-' * 60}")

        assert response.phase_type == expected_type, f"스토리: {story[:30]}..."

    total_accuracy = correct_count / len(sample_stories) if sample_stories else 0
    total_elapsed = time.perf_counter() - total_start_time

    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"kdl_bert_{now_str}.json"

    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accuracy": round(total_accuracy, 2),
        "total_time": round(total_elapsed, 2),
        "model_info": "BERT-v2-langgraph-json",
        "details": test_results,
    }

    target_path = log_dir / file_name
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with capsys.disabled():
        print(f"\n✨ 개별 테스트 로그 저장 완료: {target_path}")
        print(f"📊 최종 정확도: {total_accuracy:.2%}")
        print(f"⏱️  총 소요 시간: {total_elapsed:.2f}초")
        print(f"{'=' * 60}")
