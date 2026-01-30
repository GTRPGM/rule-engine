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


class ExplorationHandler(PhaseHandler):
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
            npcs,
            enemies,
            items,
            objs,
        ) = await self._categorize_entities(request.entities)
        # 탐험 활동에 따른 관계 변화 로직 구현
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        player_point = 2  # 플레이어 능력 - 보정치 (미정) - 임의값

        print("주사위 판정 시작")
        dice_result = await gm_service.rolling_dice(player_point, 6)
        print(
            f"[주사위 결과] 성공: {dice_result.is_success} | 크리티컬: {dice_result.is_critical_success}"
        )

        if dice_result.is_success:
            print("[주사위 결과] 성공")
            if len(items) > 0:
                for new_item in items:
                    diffs.append(
                        EntityDiff(
                            state_entity_id=player_id,
                            diff={
                                "item_entity_id": new_item.state_entity_id,
                                "quantity": (
                                    new_item.quantity
                                    if new_item.quantity is not None
                                    else 1
                                ),
                            },
                        )
                    )

                    relations.append(
                        UpdateRelation(
                            cause_entity_id=player_id,
                            effect_entity_id=new_item.state_entity_id,
                            type=RelationType.OWNERSHIP,
                        )
                    )
                print(f"{len(items)}개 아이템을 습득했니다.")

            if len(npcs) > 0:
                for new_npc in npcs:
                    diffs.append(
                        EntityDiff(
                            state_entity_id=player_id,
                            diff={
                                "state_entity_id": new_npc.state_entity_id,
                                "affinity_score": (
                                    21 if dice_result.is_critical_success else 0
                                ),
                            },
                        )
                    )

                    relations.append(
                        UpdateRelation(
                            cause_entity_id=player_id,
                            effect_entity_id=new_npc.state_entity_id,
                            type=(
                                RelationType.LITTLE_FRIENDLY
                                if dice_result.is_critical_success
                                else RelationType.NEUTRAL
                            ),
                        )
                    )
                print(
                    f"{len(npcs)}명의 NPC와 {RelationType.LITTLE_FRIENDLY if dice_result.is_critical_success else RelationType.NEUTRAL} 관계를 맺었습니다."
                )

        else:
            if len(npcs) > 0:
                for new_npc in npcs:
                    diffs.append(
                        EntityDiff(
                            state_entity_id=player_id,
                            diff={
                                "state_entity_id": new_npc.state_entity_id,
                                "affinity_score": -60,
                            },
                        )
                    )
                    relations.append(
                        UpdateRelation(
                            cause_entity_id=player_id,
                            effect_entity_id=new_npc.state_entity_id,
                            type=RelationType.LITTLE_HOSTILE,
                        )
                    )
                print(
                    f"{len(npcs)}명의 NPC와 {RelationType.LITTLE_HOSTILE} 관계를 맺었습니다."
                )

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=dice_result.is_success,
        )
