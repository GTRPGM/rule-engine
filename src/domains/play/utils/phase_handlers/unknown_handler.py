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
from utils.logger import rule


class UnknownHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
        llm: LLMManager,
    ) -> HandlerUpdatePhase:
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        dice = await gm_service.rolling_dice(2, 6)
        dice_result_log = f"이해할 수 없는 행동... {dice.message}{' | 잭팟!!' if dice.is_critical_success else ''} | 굴림값 {dice.roll_result} + 능력보정치 {dice.ability_score} = 총합 {dice.total}"
        rule(dice_result_log)

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=dice.is_success,
            logs=[dice_result_log],
        )
