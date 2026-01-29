from typing import List

from configs.llm_manager import LLMManager
from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityDiff,
    PhaseUpdate,
    PlaySceneRequest,
    RelationType,
    SceneAnalysis,
    UpdateRelation,
)
from src.domains.play.utils.phase_handlers.phase_handler_base import PhaseHandler


class ExplorationHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
        llm: LLMManager
    ) -> PhaseUpdate:
        (
            player_id,
            player_state,
            npcs,
            enemies,
            items,
            objs,
        ) = await self._categorize_entities(request.entities)
        # 탐험 활동에 따른 관계 변화 로직 구현
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        print("주사위 판정 시작")
        print(f"player → {player_state.player}")

        # mock
        relations.append(
            UpdateRelation(
                cause_entity_id=1,
                effect_entity_id=4,
                type=RelationType.LITTLE_FRIENDLY,
            ),
        )

        relations.append(
            UpdateRelation(
                cause_entity_id=1,
                effect_entity_id=5,
                type=RelationType.LITTLE_FRIENDLY,
            ),
        )

        return PhaseUpdate(diffs=diffs, relations=relations)