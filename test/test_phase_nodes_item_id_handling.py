from types import SimpleNamespace

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
    RelationType,
    UpdateRelation,
)
from domains.play.dtos.player_dtos import FullPlayerState, ItemBase, PlayerStateResponse
from domains.play.utils.phase_nodes.combat_node import combat_node
from domains.play.utils.phase_nodes.recovery_node import recovery_node


class StubItemService(ItemService):
    def __init__(self):
        super().__init__(cursor=None)

    async def get_items(self, item_ids, skip, limit):
        raise AssertionError("string item_id fallback path should not query DB items")


class StubEnemyService(EnemyService):
    def __init__(self):
        super().__init__(cursor=None)

    async def get_enemies(self, enemy_ids, skip, limit):
        return [{"enemy_id": 9001, "base_difficulty": 6}], None


class StubGmService(GmService):
    def __init__(self):
        super().__init__(cursor=None)

    async def rolling_dice(self, *_args, **_kwargs):
        return SimpleNamespace(
            message="테스트",
            is_critical_success=False,
            roll_result=4,
            ability_score=0,
            total=4,
            is_success=True,
        )


class DummyLLM:
    async def ainvoke(self, _prompt):
        return SimpleNamespace(content="없음")


class StubWorldService(WorldService):
    def __init__(self):
        super().__init__(cursor=None)


def _base_request(entities, relations, story):
    return PlaySceneRequest(
        session_id="sess-1",
        scenario_id="scn-1",
        locale_id=1,
        entities=entities,
        relations=relations,
        story=story,
    )


@pytest.mark.asyncio
async def test_combat_node_accepts_string_item_ids_and_produces_enemy_hp_diff():
    player_id = "player-1"
    enemy_state_id = "enemy-1"
    request = _base_request(
        entities=[
            EntityUnit(
                state_entity_id=player_id,
                phase_id=1,
                entity_name="플레이어",
                entity_type=EntityType.PLAYER,
            ),
            EntityUnit(
                state_entity_id=enemy_state_id,
                entity_id=9001,
                phase_id=1,
                entity_name="고블린",
                entity_type=EntityType.ENEMY,
            ),
        ],
        relations=[
            UpdateRelation(
                cause_entity_id=player_id,
                effect_entity_id=enemy_state_id,
                type=RelationType.HOSTILE,
            )
        ],
        story="플레이어가 고블린에게 검을 휘둘렀다.",
    )
    player_state = FullPlayerState(
        player=PlayerStateResponse(
            hp=30,
            gold=0,
            items=[
                ItemBase(
                    item_id="item-iron-sword-1",
                    name="철검",
                    description="검",
                    item_type="equipment",
                    meta={"effect_value": 8},
                    is_stackable=False,
                )
            ],
        ),
        player_npc_relations=[],
    )

    state = PlaySessionState(
        request=request,
        player_state=player_state,
        current_player_id=player_id,
        item_service=StubItemService(),
        enemy_service=StubEnemyService(),
        gm_service=StubGmService(),
        world_service=StubWorldService(),
        llm=DummyLLM(),
    )

    result = await combat_node(state)

    assert result["is_success"] is True
    assert result["diffs"]
    assert result["diffs"][0].state_entity_id == enemy_state_id
    assert result["diffs"][0].diff["hp"] < 0


@pytest.mark.asyncio
async def test_recovery_node_accepts_string_item_ids_and_applies_heal():
    player_id = "player-1"
    potion_id = "item-healing-potion-1"
    request = _base_request(
        entities=[
            EntityUnit(
                state_entity_id=player_id,
                phase_id=1,
                entity_name="플레이어",
                entity_type=EntityType.PLAYER,
            )
        ],
        relations=[
            UpdateRelation(
                cause_entity_id=player_id,
                effect_entity_id=potion_id,
                type=RelationType.CONSUME,
            )
        ],
        story="플레이어가 회복 포션을 마셨다.",
    )
    player_state = FullPlayerState(
        player=PlayerStateResponse(
            hp=10,
            gold=0,
            items=[
                ItemBase(
                    item_id=potion_id,
                    name="회복 포션",
                    description="회복용",
                    item_type="consumable",
                    meta={"heal_amount": 5},
                    is_stackable=True,
                )
            ],
        ),
        player_npc_relations=[],
    )
    state = PlaySessionState(
        request=request,
        player_state=player_state,
        current_player_id=player_id,
        item_service=StubItemService(),
        enemy_service=StubEnemyService(),
        gm_service=StubGmService(),
        world_service=StubWorldService(),
        llm=DummyLLM(),
    )

    result = await recovery_node(state)

    assert result["is_success"] is True
    assert any(
        d.state_entity_id == player_id and d.diff.get("hp", 0) > 0
        for d in result["diffs"]
    )
    assert any(
        rel.type == RelationType.CONSUME and rel.effect_entity_id == potion_id
        for rel in result["relations"]
    )
