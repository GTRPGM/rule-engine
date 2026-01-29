from typing import List

from src.configs.llm_manager import LLMManager
from src.domains.gm.gm_service import GmService
from src.domains.info.enemy_service import EnemyService
from src.domains.info.item_service import ItemService
from src.domains.play.dtos.play_dtos import (
    EntityDiff,
    HandlerUpdatePhase,
    PhaseUpdate,
    PlaySceneRequest,
    SceneAnalysis,
    UpdateRelation,
)
from src.domains.play.utils.phase_handlers.phase_handler_base import PhaseHandler


class UnknownHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
        llm: LLMManager
    ) -> HandlerUpdatePhase:
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=False,
        )