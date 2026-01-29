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
from src.domains.play.prompts.potion_selection_prompt import (
    create_potion_selection_prompt,
)
from src.domains.play.utils.phase_handlers.phase_handler_base import PhaseHandler


class ConsumePotionHandler(PhaseHandler):
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

        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []
        is_success = False

        if not player_id or not player_state:
            return HandlerUpdatePhase(
                update=PhaseUpdate(diffs=diffs, relations=relations),
                is_success=is_success,
            )

        # 1. 플레이어 인벤토리에서 포션 찾기
        item_ids = [int(item.item_id) for item in player_state.player.items]
        items, _ = await item_service.get_items(item_ids=item_ids, skip=0, limit=100)
        print(f"보유 아이템 목록: {items}")

        heal_items = [
            item
            for item in items
            if "소모품" == item["type"] and "포션" in item["name"]
        ]

        print(f"포션 목록: {heal_items}")

        consumed_potion = None
        effect_value: int = 0

        if heal_items:
            is_success = True  # 포션이 있다면 포션 사용은 항상 성공합니다.
            if len(heal_items) > 1:
                potion_names = [item["name"] for item in heal_items]
                prompt = create_potion_selection_prompt(potion_names, request.story)

                try:
                    llm_response = await llm.invoke(prompt)
                    potion_name_from_llm = llm_response.content.strip()
                    found_potion = next(
                        (item for item in heal_items if item["name"] == potion_name_from_llm),
                        None,
                    )
                    if found_potion:
                        consumed_potion = found_potion
                    else:
                        consumed_potion = heal_items[0]
                except Exception:
                    consumed_potion = heal_items[0]
            else:
                consumed_potion = heal_items[0]

            if consumed_potion:
                effect_value = consumed_potion["effect_value"]

        # 2. 추가 치유량 계산
        additional_heal_point: int = 0
        heal_point = 2
        if effect_value > 0:
            dice_result = await gm_service.rolling_dice(heal_point, effect_value)
            if dice_result.is_critical_success:
                additional_heal_point = heal_point * 2
                print("[주사위 결과] 크리티컬")
            elif dice_result.is_success:
                additional_heal_point = heal_point
                print("[주사위 결과] 성공")

        # 3. diffs 생성
        if consumed_potion and effect_value > 0:
            total_healing = effect_value + additional_heal_point
            diffs.append(
                EntityDiff(state_entity_id=player_id, diff={"hp": total_healing})
            )

            print(f"[치유 계산] 포션 기본 회복량: {effect_value}")
            if additional_heal_point > 0:
                print(f"[치유 계산] 주사위 추가 회복량: {additional_heal_point}")
            print(f"[치유 계산] 총 치유량: {total_healing}")

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=is_success,
        )