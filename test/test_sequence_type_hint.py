from unittest.mock import MagicMock

import pytest

from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.info.world_service import WorldService
from domains.play.dtos.play_dtos import (
    EntityType,
    EntityUnit,
    PlaySceneRequest,
    PlaySessionState,
    PhaseType,
)
from domains.play.utils.nodes import _phase_from_sequence_type, analyze_scene_node


def test_phase_from_sequence_type_mapping():
    assert _phase_from_sequence_type("BOSS_COMBAT") == PhaseType.COMBAT
    assert _phase_from_sequence_type("NEGOTIATION") == PhaseType.NEGO
    assert _phase_from_sequence_type("INFILTRATION") == PhaseType.EXPLORATION
    assert _phase_from_sequence_type("DIALOGUE") == PhaseType.DIALOGUE


@pytest.mark.asyncio
async def test_analyze_scene_node_uses_sequence_type_hint():
    cursor = MagicMock()
    req = PlaySceneRequest(
        session_id="s1",
        scenario_id="sc1",
        locale_id=0,
        sequence_type="NEGOTIATION",
        entities=[
            EntityUnit(
                state_entity_id="player-1",
                phase_id=1,
                entity_name="player",
                entity_type=EntityType.PLAYER,
            )
        ],
        relations=[],
        story="test story",
    )
    state = PlaySessionState(
        request=req,
        logs=[],
        item_service=ItemService(cursor=cursor),
        enemy_service=EnemyService(cursor=cursor),
        gm_service=GmService(cursor=cursor),
        world_service=WorldService(cursor=cursor),
        llm=MagicMock(),
    )

    result = await analyze_scene_node(state)
    analysis = result["analysis"]
    assert analysis.phase_type == PhaseType.NEGO
    assert "sequence_type hint applied" in analysis.reason
    assert analysis.confidence == 1.0
