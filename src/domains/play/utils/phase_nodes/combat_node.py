from typing import Any, Dict, List

from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityDiff,
    EntityType,
    PlaySessionState,
    RelationType,
)
from utils.logger import rule


async def combat_node(state: PlaySessionState) -> Dict[str, Any]:
    """
    전투 페이즈 로직을 처리합니다.
    """
    logs = state.logs[:]
    item_service: ItemService = state.item_service
    enemy_service: EnemyService = state.enemy_service
    gm_service: GmService = state.gm_service

    player_id = state.current_player_id
    player_state = state.player_state

    # 분류된 적 추출
    entities_in_request = state.request.entities
    enemies = [e for e in entities_in_request if e.entity_type == EntityType.ENEMY]

    if not player_id or not player_state:
        logs.append("전투 페이즈: 플레이어 정보를 찾을 수 없습니다.")
        return {
            "diffs": state.diffs,
            "relations": state.relations,
            "is_success": False,
            "logs": logs,
        }

    # 적 상세정보 조회
    combat_enemies_info = []
    enemy_state_ids = {
        (
            rel.effect_entity_id
            if rel.cause_entity_id == player_id
            else rel.cause_entity_id
        )
        for rel in state.request.relations
        if rel.type == RelationType.HOSTILE
        and (rel.cause_entity_id == player_id or rel.effect_entity_id == player_id)
    }

    enemy_id_map = {
        e.state_entity_id: e.entity_id
        for e in entities_in_request
        if e.state_entity_id in enemy_state_ids and e.entity_id is not None
    }

    enemy_rdb_ids = list(set([e.entity_id for e in enemies if e.entity_id is not None]))
    enemies_data, _ = await enemy_service.get_enemies(
        enemy_ids=enemy_rdb_ids, skip=0, limit=100
    )
    enemy_details_map = {e["enemy_id"]: e for e in enemies_data}

    for state_id in enemy_state_ids:
        rdb_id = enemy_id_map.get(state_id)
        if rdb_id:
            enemy_data = enemy_details_map.get(rdb_id)
            if enemy_data and "base_difficulty" in enemy_data:
                combat_enemies_info.append(
                    {
                        "rdb_id": rdb_id,
                        "state_id": state_id,
                        "base_difficulty": enemy_data["base_difficulty"],
                    }
                )

    # 플레이어 전투력 계산
    combat_logs: List[str] = []
    dice = await gm_service.rolling_dice(2, 6)
    dice_result_log = f"전투 시도... {dice.message}{' | 잭팟!!' if dice.is_critical_success else ''} | 굴림값 {dice.roll_result} + 능력보정치 {dice.ability_score} = 총합 {dice.total}"
    rule(dice_result_log)
    combat_logs.append(dice_result_log)

    combat_items_effect = 0
    item_ids = [int(item.item_id) for item in player_state.player.items]
    if len(item_ids) > 0:
        items, _ = await item_service.get_items(item_ids=item_ids, skip=0, limit=100)
        combat_items_effect = sum(
            item["effect_value"] for item in items if item["type"] in ("무기", "방어구")
        )

    ability_score = 2  # Hardcoded
    player_combat_power = combat_items_effect + ability_score + dice.total
    combat_judge_log = f"[전투 판정] 주사위: {dice.total}, 아이템: {combat_items_effect}, 능력치: {ability_score}"
    total_player_power_log = f"최종 플레이어 전투력: {player_combat_power}"
    rule(combat_judge_log)
    rule(total_player_power_log)
    combat_logs.append(combat_judge_log)
    combat_logs.append(total_player_power_log)
    logs.extend(combat_logs)

    # 피해 계산 및 결과 생성
    diffs: List[EntityDiff] = []
    is_success = False

    for enemy_info in combat_enemies_info:
        enemy_state_id = enemy_info["state_id"]
        enemy_difficulty = enemy_info["base_difficulty"]
        logs.append(f"적 식별번호: {enemy_state_id} | 적 전투력: {enemy_difficulty}")
        rule(f"적 식별번호: {enemy_state_id} | 적 전투력: {enemy_difficulty}")

        power_gap = player_combat_power - enemy_difficulty
        result_text = (
            "승리" if power_gap > 0 else ("무승부" if power_gap == 0 else "패배")
        )
        logs.append(f"전투 결과: {result_text} | 전투력 차이: {power_gap}")
        rule(f"전투 결과: {result_text} | 전투력 차이: {power_gap}")

        if power_gap > 0:
            is_success = True
            new_diff = EntityDiff(
                state_entity_id=enemy_state_id,
                diff={"hp": -power_gap},
            )
            diffs.append(new_diff)
            logs.append(f"전투 승리! 적에게 {power_gap}의 데미지를 입혔습니다.")

        elif power_gap < 0:
            is_success = False
            new_diff = EntityDiff(
                state_entity_id=player_id,
                diff={"hp": power_gap},
            )
            diffs.append(new_diff)
            logs.append(f"전투 패배... 플레이어가 {-power_gap}의 데미지를 입었습니다.")
        else:
            logs.append("막상막하의 대결이었습니다!")

    return {
        "diffs": diffs,
        "relations": state.relations,  # 관계는 전투 핸들러에서 직접 업데이트되지 않고 통과
        "is_success": is_success,
        "logs": logs,
    }
