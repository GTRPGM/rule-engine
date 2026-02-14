import asyncio
import datetime
import json
import os
import random
import time
import unittest
from unittest.mock import create_autospec

from configs.llm_manager import LLMManager
from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.info.world_service import WorldService
from domains.play.dtos.play_dtos import PhaseType, PlaySceneRequest, PlaySessionState
from domains.play.utils.nodes import analyze_scene_node


class TestAnalyzeSceneNode(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Load sample stories from JSON
        json_file_path = os.path.join(
            os.path.dirname(__file__), "sample_stories", "sample_stories.json"
        )
        with open(json_file_path, "r", encoding="utf-8") as f:
            raw_stories = json.load(f)

        self.sample_stories = []
        for item in raw_stories:
            self.sample_stories.append((PhaseType(item["phase_type"]), item["story"]))

        # Randomly select 100 stories if more than 100 exist
        if len(self.sample_stories) > 100:
            self.sample_stories = random.sample(self.sample_stories, 100)

        # Pydantic의 타입 검증을 통과하기 위해 create_autospec 사용
        # spec_set=True는 실제 클래스에 없는 속성에 접근할 때 에러를 발생시킵니다.
        self.mock_item_service = create_autospec(
            ItemService, instance=True, spec_set=True
        )
        self.mock_enemy_service = create_autospec(
            EnemyService, instance=True, spec_set=True
        )
        self.mock_gm_service = create_autospec(GmService, instance=True, spec_set=True)
        self.mock_world_service = create_autospec(
            WorldService, instance=True, spec_set=True
        )

        # 테스트에 필요한 LLM 매니저를 초기화합니다.
        self.llm_manager = LLMManager.get_instance("gateway")

    async def test_analyze_scene_node_logic(self):
        print(
            f"\n{'=' * 60}\n LLM 기반 장면 분석 노드 성능 및 정확도 테스트 시작\n{'=' * 60}"
        )

        correct_predictions = 0
        total_predictions = len(self.sample_stories)
        all_details = []
        total_elapsed_time = 0.0

        for expected_type, story in self.sample_stories:
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
                    logs=[],
                )

                # 2. 시간 측정 시작
                start_time = time.perf_counter()

                # 3. `analyze_scene_node` 실행
                result_dict = await analyze_scene_node(state)
                analysis = result_dict.get("analysis")

                # 4. 시간 측정 종료
                end_time = time.perf_counter()
                elapsed = end_time - start_time
                total_elapsed_time += elapsed

                # 5. 결과 검증 및 출력
                self.assertIsNotNone(analysis)
                is_correct = analysis.phase_type == expected_type
                print(f"\n[입력 문장]: {story_cleaned}")
                print(
                    f"[결과] 정답: {expected_type.value} | 예상: {analysis.phase_type.value}"
                )
                print(f"[소요 시간]: {elapsed:.2f}초")
                print(f"[분석 이유]: {analysis.reason}")
                print(f"{'-' * 60}")

                if is_correct:
                    correct_predictions += 1

                # Collect details for JSON output
                all_details.append(
                    {
                        "story": story_cleaned,
                        "expected": expected_type.value,
                        "actual": analysis.phase_type.value,
                        "is_correct": is_correct,
                        "confidence": analysis.confidence,
                        "reason": analysis.reason,
                        "elapsed": elapsed,
                    }
                )

        accuracy = (
            (correct_predictions / total_predictions) * 100
            if total_predictions > 0
            else 0
        )
        print(f"\n{'=' * 60}")
        print(" LLM 기반 장면 분석 노드 성능 및 정확도 테스트 완료")
        print(f" 전체 테스트 케이스 수: {total_predictions}")
        print(f" 정확한 예측 수: {correct_predictions}")
        print(f" 전체 정확도: {accuracy:.2f}%")
        print(f"{'=' * 60}")

        # Determine model info
        model_info = "unknown"
        if hasattr(self.llm_manager, "model_name"):
            model_info = self.llm_manager.model_name
        elif hasattr(self.llm_manager, "model"):
            model_info = self.llm_manager.model
        # Special handling for NarrativeChatModel (gateway)
        elif hasattr(LLMManager, "_instances") and "gateway" in LLMManager._instances:
            # Get the type of the 'gateway' instance to compare with self.llm_manager's type
            gateway_instance = LLMManager._instances["gateway"]
            if isinstance(self.llm_manager, type(gateway_instance)):
                model_info = "gateway"

        # Prepare final test results dictionary
        test_results = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "accuracy": round(
                accuracy / 100, 2
            ),  # Convert percentage to a fraction and round
            "total_time": round(total_elapsed_time, 2),
            "model_info": model_info,
            "details": all_details,
        }

        # Save results to JSON file
        results_dir = os.path.join(os.path.dirname(__file__), "test_results")
        os.makedirs(results_dir, exist_ok=True)  # Ensure directory exists
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"llm_classification_{timestamp_str}.json"
        file_path = os.path.join(results_dir, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)

        print(f"\n테스트 결과가 다음 파일에 저장되었습니다: {file_path}")

    async def asyncTearDown(self):
        # 각 테스트 후 약간의 지연 시간을 주어 리소스 정리 시간을 확보합니다.
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    unittest.main()
