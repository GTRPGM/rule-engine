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
from domains.play.dtos.player_dtos import FullPlayerState, PlayerStateResponse
from domains.play.utils.phase_nodes.exploration_node import exploration_node

# Stub classes
class StubGmService(GmService):
    def __init__(self):
        self.cursor = None

    async def rolling_dice(self, *_args, **_kwargs):
        # Always succeed for test consistency
        return SimpleNamespace(
            message="Test Roll",
            is_critical_success=False,
            roll_result=10,
            ability_score=0,
            total=10,
            is_success=True,
        )

class StubItemService(ItemService):
    def __init__(self):
        self.cursor = None

class StubEnemyService(EnemyService):
    def __init__(self):
        self.cursor = None

class StubWorldService(WorldService):
    def __init__(self):
        self.cursor = None

class MockLLM:
    pass

@pytest.mark.asyncio
async def test_exploration_node_creates_relation_for_new_npc():
    # Given: Player meets a new NPC during exploration
    player_id = "player-1"
    npc_id = "npc-new-exploration-1"
    
    entities = [
        EntityUnit(state_entity_id=player_id, phase_id=1, entity_name="Player", entity_type=EntityType.PLAYER),
        EntityUnit(state_entity_id=npc_id, phase_id=1, entity_name="New NPC", entity_type=EntityType.NPC)
    ]
    
    relations = []
    
    request = PlaySceneRequest(
        session_id="sess-1",
        scenario_id="scn-1",
        locale_id=1,
        target="",
        entities=entities,
        relations=relations,
        story="Found a new NPC!",
    )
    
    player_state = FullPlayerState(
        player=PlayerStateResponse(hp=10, gold=0, items=[]),
        player_npc_relations=[] # No prior relations
    )
    
    state = PlaySessionState(
        request=request,
        player_state=player_state,
        current_player_id=player_id,
        item_service=StubItemService(),
        enemy_service=StubEnemyService(),
        gm_service=StubGmService(),
        world_service=StubWorldService(),
        llm=MockLLM(),
    )
    
    # When: exploration_node is executed
    result = await exploration_node(state)
    
    # Then: A new relation should be created for the NPC
    assert result["is_success"] is True
    
    new_relations = result["relations"]
    
    # Check if we have a relation for the new NPC
    npc_relations = [r for r in new_relations if r.effect_entity_id == npc_id]
    
    assert len(npc_relations) == 1
    rel = npc_relations[0]
    assert rel.cause_entity_id == player_id
    assert rel.type == RelationType.NEUTRAL