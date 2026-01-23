import asyncio
import time  # 시간 측정을 위해 추가
import unittest
from unittest.mock import MagicMock

from domains.play.play_service import PlayService, PlayType

# 샘플 데이터 정의 (기존과 동일)
SAMPLE_STORIES = [
    (
        PlayType.BATTLE,
        "어둠 속에서 갑자기 고블린 무리가 무딘 단검을 휘두르며 달려듭니다.",
    ),
    (PlayType.NEGOTIATE, "성문 앞 경비병이 통행료로 100골드를 요구합니다."),
    (PlayType.EXPLORE, "오래된 유적의 벽면에 새겨진 기괴한 문양을 조사합니다."),
    (
        PlayType.BATTLE,
        "주점에서 술을 마시던 중, 옆 테이블의 용병과 시비가 붙었습니다...",
    ),  # 중략
    (PlayType.NEGOTIATE, "상인 길드장에게 희귀 약초를 팔려고 합니다..."),  # 중략
    (PlayType.EXPLORE, "안개 낀 늪지대에서 길을 잃었습니다..."),  # 중략
    (
        PlayType.UNKNOWN,
        "배가 고파진 당신은 가방을 열어 딱딱한 빵 한 조각을 꺼내 씹어 먹습니다...",
    ),
    (
        PlayType.UNKNOWN,
        "오늘 날씨가 참 좋군요. 당신은 성벽 위를 거닐며 멀리 보이는 산맥을 바라봅니다...",
    ),
    (
        PlayType.BATTLE,
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

    async def test_analyze_scene_logic(self):
        print(f"\n{'=' * 60}\n 로컬 LLM(Ollama) 성능 및 정확도 테스트 시작\n{'=' * 60}")

        for expected_type, story in SAMPLE_STORIES:
            with self.subTest(story=story[:20]):  # 요약해서 표시
                # 1. 시간 측정 시작
                start_time = time.perf_counter()
                print("test expected_type")
                print(expected_type)
                print("test story")
                print(story)
                # 2. Execute
                result = await self.service.analyze_scene(story)

                # 3. 시간 측정 종료
                end_time = time.perf_counter()
                elapsed = end_time - start_time

                # 4. 결과 출력
                print(f"\n[입력 문장]: {story}")
                print(
                    f"[결과] 예상: {expected_type.value} | 실제: {result.play_type.value}"
                )
                print(f"[소요 시간]: {elapsed:.2f}초")
                print(f"[분석 이유]: {result.reason}")
                print(f"{'-' * 60}")

                # 5. Assert
                self.assertEqual(result.play_type, expected_type)

    async def asyncTearDown(self):
        await asyncio.sleep(0.5)
