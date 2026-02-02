import asyncio
import json
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from domains.play.dtos.play_dtos import PhaseType
from domains.play.play_service import PlayService

# 샘플 데이터 정의 (기존과 동일)
SAMPLE_STORIES = [
    (
        PhaseType.COMBAT,
        "어둠 속에서 갑자기 고블린 무리가 무딘 단검을 휘두르며 달려듭니다.",
    ),
    (PhaseType.DIALOGUE, "성문 앞 경비병이 통행료로 100골드를 요구합니다."),
    (PhaseType.EXPLORATION, "오래된 유적의 벽면에 새겨진 기괴한 문양을 조사합니다."),
    (
        PhaseType.COMBAT,
        "주점에서 술을 마시던 중, 옆 테이블의 용병과 시비가 붙었습니다...",
    ),  # 중략
    (PhaseType.DIALOGUE, "상인 길드장에게 희귀 약초를 팔려고 합니다..."),  # 중략
    (PhaseType.EXPLORATION, "안개 낀 늪지대에서 길을 잃었습니다..."),  # 중략
    (
        PhaseType.REST,
        "배가 고파진 당신은 가방을 열어 딱딱한 빵 한 조각을 꺼내 씹어 먹습니다...",
    ),
    (
        PhaseType.UNKNOWN,
        "오늘 날씨가 참 좋군요. 당신은 성벽 위를 거닐며 멀리 보이는 산맥을 바라봅니다...",
    ),
    (
        PhaseType.COMBAT,
        "협상을 하러 갔지만, 상대가 갑자기 탁자를 내리치며 부하들에게 신호를 보냈습니다!...",
    ),
]


class TestPlayService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_cursor = MagicMock()
        self.service = PlayService(
            cursor=self.mock_cursor,
            llm_provider="gateway",
        )
        self.test_results = []
        self.log_dir = Path("test_logs")
        self.log_dir.mkdir(exist_ok=True)

    async def test_analyze_scene_logic(self):
        print(f"\n{'=' * 60}\n LLM 성능 및 정확도 테스트 시작\n{'=' * 60}")

        correct_count = 0
        total_start_time = time.perf_counter()

        for expected_type, story in SAMPLE_STORIES:
            with self.subTest(story=story[:20]):
                start_time = time.perf_counter()
                result = await self.service.analyze_scene(story)
                elapsed = time.perf_counter() - start_time

                is_correct = result.phase_type == expected_type
                if is_correct:
                    correct_count += 1

                # 개별 결과 기록
                case_result = {
                    "story": story,
                    "expected": expected_type.name,
                    "actual": result.phase_type.name,
                    "is_correct": is_correct,
                    "confidence": getattr(
                        result, "confidence", 0
                    ),  # 신뢰도 필드가 있다면 포함
                    "reason": result.reason,
                    "elapsed": round(elapsed, 3),
                }
                self.test_results.append(case_result)

                print(f"\n[입력]: {story}")
                print(
                    f"[결과] 정답: {expected_type.name} | 예상: {result.phase_type.name} ({'PASS' if is_correct else 'FAIL'})"
                )
                print(
                    f"[신뢰도]: {case_result['confidence']:.2f} | 소요시간: {elapsed:.2f}초"
                )
                print(f"{'-' * 60}")

                self.assertEqual(result.phase_type, expected_type)

        self.total_accuracy = correct_count / len(SAMPLE_STORIES)
        self.total_elapsed = time.perf_counter() - total_start_time

    async def asyncTearDown(self):
        # 테스트 종료 후 로그 파일 저장
        if hasattr(self, "test_results") and self.test_results:
            # 1. 파일명에 사용할 타임스탬프 생성 (예: 20240522_143005)
            now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"kdl_bert_{now_str}.json"

            report = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "accuracy": round(self.total_accuracy, 2),
                "total_time": round(self.total_elapsed, 2),
                "model_info": "BERT-v2",
                "details": self.test_results,
            }

            # 2. 지정된 파일명으로 개별 저장
            target_path = self.log_dir / file_name

            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"\n✨ 개별 테스트 로그 저장 완료: {target_path}")
            print(f"📊 최종 정확도: {self.total_accuracy:.2%}")

        await asyncio.sleep(0.5)

        await asyncio.sleep(0.5)
