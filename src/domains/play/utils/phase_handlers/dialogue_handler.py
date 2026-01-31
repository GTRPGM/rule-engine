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
    RelationType,
    SceneAnalysis,
    UpdateRelation,
)
from src.domains.play.utils.phase_handlers.phase_handler_base import PhaseHandler
from utils.logger import rule


class DialogueHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
        llm: LLMManager,
    ) -> HandlerUpdatePhase:
        logs: List[str] = []
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        social_ability = 3  # 플레이어의 사교 능력치 (임시값)

        (
            player_id,
            player_state,
            npcs,
            enemies,
            items,
            objs,
        ) = await self._categorize_entities(request.entities)

        target_npc_state_id = None
        initial_affinity_score = 0

        # 1. request.relations 목록에서 npc를 찾아 affinity_score 추출하기
        for npc_entity in npcs:
            for rel in request.relations:
                if (
                    rel.cause_entity_id == player_id
                    and rel.effect_entity_id == npc_entity.state_entity_id
                ) or (
                    rel.effect_entity_id == player_id
                    and rel.cause_entity_id == npc_entity.state_entity_id
                ):
                    target_npc_state_id = npc_entity.state_entity_id
                    if rel.affinity_score is not None:
                        initial_affinity_score = rel.affinity_score
                    break
            if target_npc_state_id:
                break

        # 2. affinity_score를 주사위 난이도로 설정하기
        # NPC를 찾을 수 없으면, 기본값 사용
        if not target_npc_state_id:
            affinity_difficulty = -5  # 관계가 없다면 -5로 가정
            rule("상호작용중인 NPC가 없습니다. 기본 우호도로 주사위를 굴립니다.")
            logs.append("상호작용중인 NPC가 없습니다. 기본 우호도로 주사위를 굴립니다.")
        else:
            # affinity_score를 주사위 난이도로 설정 (높은 우호도가 낮은 난이도)
            affinity_difficulty = -initial_affinity_score
            affinity_score_log = f"NPC {target_npc_state_id}의 초기 우호도: {initial_affinity_score}, 설정 난이도: {affinity_difficulty}"
            rule(affinity_score_log)
            logs.append(affinity_score_log)

        dice_result = await gm_service.rolling_dice(social_ability, affinity_difficulty)
        dice_result_log = f"대화 시도... {dice_result.message}{' | 잭팟!!' if dice_result.is_critical_success else ''} | 굴림값 {dice_result.roll_result} + 능력보정치 {dice_result.ability_score} = 총합 {dice_result.total}"

        rule(dice_result_log)
        logs.append(dice_result_log)

        # 3. 주사위 차이만큼 우호도 계산해 NPC의 우호도 변경량을 diffs에 반영하기
        if target_npc_state_id:
            affinity_change_amount = 0
            roll_difference = dice_result.total - affinity_difficulty

            if dice_result.is_success:
                affinity_change_amount = max(1, roll_difference)
                success_log = (
                    f"대화 성공! NPC 우호도가 {affinity_change_amount}만큼 증가합니다."
                )
                rule(success_log)
                logs.append(success_log)
            else:
                affinity_change_amount = min(-1, roll_difference)
                fail_log = f"대화 실패! NPC 우호도가 {abs(affinity_change_amount)}만큼 감소합니다."
                rule(fail_log)
                logs.append(fail_log)

            # 우호도 등급 변경 확인
            total_affinity = initial_affinity_score + affinity_change_amount

            relation_grade: RelationType

            if -100 <= total_affinity <= -61:
                relation_grade = RelationType.HOSTILE
            elif -60 <= total_affinity <= -21:
                relation_grade = RelationType.LITTLE_HOSTILE
            elif -20 <= total_affinity <= 20:
                relation_grade = RelationType.NEUTRAL
            elif 21 <= total_affinity <= 60:
                relation_grade = RelationType.LITTLE_FRIENDLY
            elif 61 <= total_affinity <= 100:
                relation_grade = RelationType.FRIENDLY
            else:
                if total_affinity < -100:
                    relation_grade = RelationType.HOSTILE
                elif total_affinity > 100:
                    relation_grade = RelationType.FRIENDLY
                else:
                    relation_grade = RelationType.NEUTRAL

            diffs.append(
                EntityDiff(
                    state_entity_id=target_npc_state_id,
                    diff={"affinity_score": affinity_change_amount},
                )
            )

            relations.append(
                UpdateRelation(
                    cause_entity_id=player_id,
                    effect_entity_id=target_npc_state_id,
                    type=relation_grade,
                    affinity_score=total_affinity,
                )
            )
        else:
            rule("대화할 NPC를 찾을 수 없어 우호도 변경을 적용하지 않습니다.")
            logs.append("대화할 NPC를 찾을 수 없어 우호도 변경을 적용하지 않습니다.")

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=dice_result.is_success,
            logs=logs,
        )
