import asyncio
import time
import unittest
from unittest.mock import MagicMock, create_autospec

from configs.llm_manager import LLMManager
from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.info.world_service import WorldService
from domains.play.dtos.play_dtos import PhaseType, PlaySceneRequest, PlaySessionState
from domains.play.utils.nodes import analyze_scene_node

# 샘플 데이터 정의
SAMPLE_STORIES = [
    (
        PhaseType.COMBAT,
        "어둠 속에서 갑자기 고블린 무리가 무딘 단검을 휘두르며 달려듭니다.",
    ),
    (PhaseType.NEGO, "성문 앞 경비병이 통행료로 100골드를 요구합니다."),
    (PhaseType.DIALOGUE, "마을 촌장 듄에게 인사를 건냅니다."),
    (PhaseType.EXPLORATION, "오래된 유적의 벽면에 새겨진 기괴한 문양을 조사합니다."),
    (
        PhaseType.DIALOGUE,
        "주점에서 술을 마시던 중, 옆 테이블의 용병과 시비가 붙었습니다...",
    ),
    (PhaseType.NEGO, "상인 길드장에게 희귀 약초를 팔려고 합니다..."),
    (
        PhaseType.DIALOGUE,
        "미치광이 마법사 수나에게 뇌물을 건냅니다.",
    ),
    (PhaseType.EXPLORATION, "안개 낀 늪지대에서 길을 잃었습니다..."),
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
        "협상을 하러 갔지만, 상대가 갑자기 탁자를 내리치며 부하들에게 신호를 보냈습니다!",
    ),
]


class TestAnalyzeSceneNode(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Pydantic의 타입 검증을 통과하기 위해 create_autospec 사용
        # spec_set=True는 실제 클래스에 없는 속성에 접근할 때 에러를 발생시킵니다.
        mock_cursor = MagicMock()
        self.mock_item_service = create_autospec(ItemService, instance=True, spec_set=True)
        self.mock_enemy_service = create_autospec(EnemyService, instance=True, spec_set=True)
        self.mock_gm_service = create_autospec(GmService, instance=True, spec_set=True)
        self.mock_world_service = create_autospec(WorldService, instance=True, spec_set=True)

        # 테스트에 필요한 LLM 매니저를 초기화합니다.
        self.llm_manager = LLMManager.get_instance("gateway")


    async def test_analyze_scene_node_logic(self):
        print(f"\n{'=' * 60}\n LLM 기반 장면 분석 노드 성능 및 정확도 테스트 시작\n{'=' * 60}")

        for expected_type, story in SAMPLE_STORIES:
            # Note: The last story in the original file had a weird character at the end.
            # I am removing it to make sure the test is clean.
            # "협상을 하러 갔지만, 상대가 갑자기 탁자를 내리치며 부하들에게 신호를 보냈습니다! súčasťou"
            story_cleaned = story.replace(" súčasťou", "")

            with self.subTest(story=story_cleaned[:30]):
                # 1. 테스트용 상태(State) 객체 생성
                request = PlaySceneRequest(
                    session_id="test-session",
                    scenario_id="test-scenario",
                    locale_id=1,
                    entities=[],
                    relations=[],
                    story=story_cleaned,
                )
                state = PlaySessionState(
                    request=request,
                    llm=self.llm_manager,
                    item_service=self.mock_item_service,
                    enemy_service=self.mock_enemy_service,
                    gm_service=self.mock_gm_service,
                    world_service=self.mock_world_service,
                    logs=[]
                )

                # 2. 시간 측정 시작
                start_time = time.perf_counter()

                # 3. `analyze_scene_node` 실행
                result_dict = await analyze_scene_node(state)
                analysis = result_dict.get("analysis")

                # 4. 시간 측정 종료
                end_time = time.perf_counter()
                elapsed = end_time - start_time

                # 5. 결과 검증 및 출력
                self.assertIsNotNone(analysis)
                print(f"\n[입력 문장]: {story_cleaned}")
                print(f"[결과] 정답: {expected_type.value} | 예상: {analysis.phase_type.value}")
                print(f"[소요 시간]: {elapsed:.2f}초")
                print(f"[분석 이유]: {analysis.reason}")
                print(f"{'-' * 60}")

                self.assertEqual(analysis.phase_type, expected_type)

    async def asyncTearDown(self):
        # 각 테스트 후 약간의 지연 시간을 주어 리소스 정리 시간을 확보합니다.
        await asyncio.sleep(0.5)

if __name__ == '__main__':
    unittest.main()