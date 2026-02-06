from typing import Any, Dict

from configs.llm_manager import LLMManager
from domains.gm.gm_service import GmService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityDiff,
    PlaySessionState,
    RelationType,
    UpdateRelation,
)
from domains.play.prompts.potion_selection_prompt import (
    create_potion_selection_prompt,
)
from utils.logger import rule


async def recovery_node(state: PlaySessionState) -> Dict[str, Any]:
    logs = state.logs[:]
    diffs = state.diffs[:]
    relations = state.relations[:]

    player_id = state.current_player_id
    player_state = state.player_state

    item_service: ItemService = state.item_service
    gm_service: GmService = state.gm_service
    llm: LLMManager = state.llm

    is_success = False

    if not player_id or not player_state:
        logs.append("회복 페이즈: 플레이어 정보를 찾을 수 없습니다.")
        return {
            "diffs": diffs,
            "relations": relations,
            "is_success": is_success,
            "logs": logs,
        }

    # 1. 플레이어 인벤토리에서 포션 찾기
    item_ids = [int(item.item_id) for item in player_state.player.items]
    heal_items = None
    if len(item_ids) > 0:
        items, _ = await item_service.get_items(item_ids=item_ids, skip=0, limit=100)

        heal_items = [
            item
            for item in items
            if "소모품" == item["type"] and "포션" in item["name"]
        ]

    consumed_potion = None
    effect_value: int = 0

    if heal_items:
        is_success = True
        if len(heal_items) > 1:
            potion_names = [item["name"] for item in heal_items]
            prompt = create_potion_selection_prompt(potion_names, state.request.story)

            try:
                llm_response = await llm.ainvoke(prompt)
                potion_name_from_llm = llm_response.content.strip()
                found_potion = next(
                    (
                        item
                        for item in heal_items
                        if item["name"] == potion_name_from_llm
                    ),
                    None,
                )
                if found_potion:
                    consumed_potion = found_potion
                else:
                    consumed_potion = heal_items[0]

                rule(
                    f"[소모 아이템 정보] {consumed_potion['name']} | 치유량: {consumed_potion['effect_value']}"
                )
                logs.append(
                    f"[소모 아이템 정보] {consumed_potion['name']} | 치유량: {consumed_potion['effect_value']}"
                )
            except Exception:
                consumed_potion = heal_items[0]
        else:
            consumed_potion = heal_items[0]

        if consumed_potion:
            effect_value = consumed_potion["effect_value"]

    else:
        logs.append("이런! 보유한 포션이 하나도 없습니다.")
        rule("이런! 보유한 포션이 하나도 없습니다.")

    # 2. 추가 치유량 계산
    additional_heal_point: int = 0
    heal_point = 2
    if effect_value > 0:
        dice_result = await gm_service.rolling_dice(heal_point, effect_value)
        dice_result_log = f"추가 치유 시도... {dice_result.message}{' | 잭팟!!' if dice_result.is_critical_success else ''} | 굴림값 {dice_result.roll_result} + 능력보정치 {dice_result.ability_score} = 총합 {dice_result.total}"
        logs.append(dice_result_log)
        rule(dice_result_log)

        if dice_result.is_critical_success:
            additional_heal_point = heal_point * 2
            additional_heal_log = (
                f"두 배 추가 치유 포인트가 적용됩니다. +{additional_heal_point} "
            )
            rule(additional_heal_log)
            logs.append(additional_heal_log)
        elif dice_result.is_success:
            additional_heal_point = heal_point
            additional_heal_log = (
                f"추가 치유 포인트가 적용됩니다. +{additional_heal_point}"
            )
            rule(additional_heal_log)
            logs.append(additional_heal_log)

    # 3. diffs 생성
    if consumed_potion and effect_value > 0:
        total_healing = effect_value + additional_heal_point
        target_portion = next(
            (
                rel
                for rel in state.request.relations
                if rel.type == RelationType.CONSUME
                and consumed_potion["item_id"] == rel.effect_entity_id
            ),
            None,
        )

        if target_portion is not None:
            player_diff = EntityDiff(
                state_entity_id=player_id, diff={"hp": total_healing}
            )
            diffs.append(player_diff)
            rule(f"diffs.append({player_diff.model_dump()})")

            consumed_potion_rel = UpdateRelation(
                cause_entity_id=player_id,
                effect_entity_id=target_portion.effect_entity_id,
                type=RelationType.CONSUME,
                quantity=-1,
            )

            relations.append(consumed_potion_rel)
            rule(f"relations.append({consumed_potion_rel.model_dump()})")

        rule(f"[치유 계산] 포션 기본 회복량: {effect_value}")
        logs.append(f"[치유 계산] 포션 기본 회복량: {effect_value}")

        if additional_heal_point > 0:
            rule(f"[치유 계산] 주사위 추가 회복량: {additional_heal_point}")
            logs.append(f"[치유 계산] 주사위 추가 회복량: {additional_heal_point}")

        rule(f"[치유 계산] 총 치유량: {total_healing}")
        logs.append(f"[치유 계산] 총 치유량: {total_healing}")

    return {
        "diffs": diffs,
        "relations": relations,
        "is_success": is_success,
        "logs": logs,
    }
