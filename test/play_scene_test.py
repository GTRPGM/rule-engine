import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domains.gm.dtos.dice_check_result import DiceCheckResult
from src.domains.play.dtos.play_dtos import (  # EntityType 임포트
    EntityType,
    PhaseType,
    PhaseUpdate,
    PlaySceneRequest,
    PlaySceneResponse,
)
from src.domains.play.play_service import PlayService
from src.domains.play.utils.dummy_player import dummy_player  # dummy_player import

# 테스트 데이터 파일 경로
TEST_DATA_DIR = Path(__file__).parent
TEST_REQUEST_FILES = [f for f in TEST_DATA_DIR.glob("play_*.json")]


# PlayService의 의존성을 모킹
@pytest.fixture
def mock_play_service():
    # LLMManager.get_instance 자체를 모킹
    with patch(
        "src.configs.llm_manager.LLMManager.get_instance"
    ) as mock_llm_manager_get_instance:
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.return_value = AsyncMock(
            return_value=MagicMock(
                phase_type=PhaseType.UNKNOWN.value, reason="test", confidence=1.0
            )
        )
        mock_llm_manager_get_instance.return_value = mock_llm_instance

        # PhaseHandlerFactory 모킹
        with patch(
            "src.domains.play.utils.phase_handler_factory.PhaseHandlerFactory.get_handler"
        ) as MockPhaseHandlerFactory:
            mock_handler = MagicMock()
            mock_handler.handle = AsyncMock(
                return_value=MagicMock(
                    update=PhaseUpdate(diffs=[], relations=[]).model_dump(),
                    is_success=True,
                    logs=["test log"],
                )
            )

            # _categorize_entities 모킹 추가 (side_effect 사용)
            async def mock_categorize_entities(entities):
                player_id = None
                for entity in entities:
                    if entity.entity_type == EntityType.PLAYER:
                        player_id = entity.state_entity_id
                        break
                return (
                    player_id,  # 실제 request.entities에서 player_id를 추출하여 반환
                    dummy_player,  # player_state (현재 dummy_player는 고정값)
                    [],  # npcs
                    [],  # enemies
                    [],  # drop_items
                    [],  # objects
                )

            mock_handler._categorize_entities = AsyncMock(
                side_effect=mock_categorize_entities
            )
            MockPhaseHandlerFactory.return_value = mock_handler

        mock_cursor = MagicMock()

        # GmService 모킹
        with patch("src.domains.gm.gm_service.GmService") as MockGmService:
            mock_gm_service_instance = MockGmService.return_value
            mock_gm_service_instance.rolling_dice = AsyncMock(
                return_value=DiceCheckResult(
                    message="테스트 주사위 결과",
                    roll_result=7,
                    total=10,
                    is_success=True,
                    is_critical_success=False,
                )
            )

            # ItemService 모킹
            with patch("src.domains.info.item_service.ItemService") as MockItemService:
                mock_item_service_instance = MockItemService.return_value
                mock_item_service_instance.get_items = AsyncMock(return_value=([], 0))

                # EnemyService 모킹
                with patch(
                    "src.domains.info.enemy_service.EnemyService"
                ) as MockEnemyService:
                    mock_enemy_service_instance = MockEnemyService.return_value

                    # WorldService 모킹
                    with patch(
                        "src.domains.info.world_service.WorldService"
                    ) as MockWorldService:
                        mock_world_service_instance = MockWorldService.return_value
                        mock_world_service_instance.get_world = AsyncMock(
                            return_value={"locales": []}
                        )

                        service = PlayService(mock_cursor)
                        service.gm_service = mock_gm_service_instance
                        service.item_service = mock_item_service_instance
                        service.enemy_service = mock_enemy_service_instance
                        service.llm = mock_llm_instance  # PlayService의 llm 속성에 모킹된 인스턴스 할당
                        service.world_service = mock_world_service_instance
                        yield service


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_file", TEST_REQUEST_FILES, ids=[f.name for f in TEST_REQUEST_FILES]
)
async def test_play_scene(mock_play_service: PlayService, request_file: Path):
    with open(request_file, "r", encoding="utf-8") as f:
        request_data = json.load(f)

    request = PlaySceneRequest(**request_data)
    response = await mock_play_service.play_scene(request)

    assert isinstance(response, PlaySceneResponse)
    assert response.session_id == request.session_id
    assert response.scenario_id == request.scenario_id
    assert response.success is True
    assert isinstance(response.suggested, PhaseUpdate)
    assert response.suggested.diffs == []
    assert response.suggested.relations == []
    assert len(response.logs) > 0
