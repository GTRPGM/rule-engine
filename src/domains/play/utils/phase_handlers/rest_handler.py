from typing import List

from configs.llm_manager import LLMManager
from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityDiff,
    HandlerUpdatePhase,
    PhaseUpdate,
    PlaySceneRequest,
    SceneAnalysis,
    UpdateRelation,
)
from src.domains.play.utils.phase_handlers.phase_handler_base import PhaseHandler


class RestHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
        llm: LLMManager,
    ) -> HandlerUpdatePhase:
        (
            player_id,
            player_state,
            _,
            _,
            _,
            _,
        ) = await self._categorize_entities(request.entities)

        logs: List[str] = []
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        heal_point = 2  # 기본 턴 당 회복량 - 임의값

        # 주사위를 굴려 heal_point 외 추가 회복량을 정합니다.
        dice_result = await gm_service.rolling_dice(heal_point, 6)
        dice_result_log = f"휴식 시도... {dice_result.message}{' | 잭팟!!' if dice_result.is_critical_success else ''} | 굴림값 {dice_result.roll_result} + 능력보정치 {dice_result.ability_score} = 총합 {dice_result.total}"
        print(dice_result_log)
        logs.append(dice_result_log)

        additional_healing: int = 0
        # 주사위 판정이 성공이고 크리티컬이면 주사위 total만큼 회복합니다.
        if dice_result.is_critical_success:
            additional_healing = dice_result.total
        # 주사위 판정이 성공이지만 크리티컬이 아니면 주사위 total의 절반(소수점 버림)만큼 회복합니다.
        elif dice_result.is_success:
            additional_healing = dice_result.total // 2
        # 주사위 판정이 실패이면 추가 회복량은 0입니다.
        else:
            additional_healing = 0

        total_healing = heal_point + additional_healing
        if dice_result.is_success:
            success_log = f"""회복 성공: {dice_result.is_success} | 총 회복량(주사위 합 {dice_result.total} {"" if dice_result.is_critical_success else "/ 2"} + 기본 회복량 {heal_point}): {total_healing}"""
            print(success_log)
            logs.append(success_log)
        else:
            fail_log = f"""회복 성공: {dice_result.is_success} | 총 회복량 = 기본 회복량 {heal_point}): {total_healing}"""
            print(fail_log)
            logs.append(fail_log)

        diffs.append(EntityDiff(state_entity_id=player_id, diff={"hp": total_healing}))

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=dice_result.is_success,
            logs=logs,
        )
