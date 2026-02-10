from typing import Any, Dict

from domains.gm.gm_service import GmService
from domains.play.dtos.play_dtos import EntityDiff, PlaySessionState
from utils.logger import rule


async def rest_node(state: PlaySessionState) -> Dict[str, Any]:
    logs = state.logs[:]
    diffs = state.diffs[:]
    relations = state.relations[:]

    player_id = state.current_player_id
    player_state = state.player_state

    gm_service: GmService = state.gm_service

    if not player_id or not player_state:
        logs.append("휴식 페이즈: 플레이어 정보를 찾을 수 없습니다.")
        return {
            "diffs": diffs,
            "relations": relations,
            "is_success": False,
            "logs": logs,
        }

    heal_point = 2

    dice_result = await gm_service.rolling_dice(heal_point, 6)
    dice_result_log = f"휴식 시도... {dice_result.message}{' | 잭팟!!' if dice_result.is_critical_success else ''} | 굴림값 {dice_result.roll_result} + 능력보정치 {dice_result.ability_score} = 총합 {dice_result.total}"
    rule(dice_result_log)
    logs.append(dice_result_log)

    additional_healing: int = 0
    if dice_result.is_critical_success:
        additional_healing = dice_result.total
    elif dice_result.is_success:
        additional_healing = dice_result.total // 2
    else:
        additional_healing = 0

    total_healing = heal_point + additional_healing
    if dice_result.is_success:
        success_log = f"""회복 성공: {dice_result.is_success} | 총 회복량(주사위 합 {dice_result.total} {"" if dice_result.is_critical_success else "/ 2"} + 기본 회복량 {heal_point}): {total_healing}"""
        rule(success_log)
        logs.append(success_log)
    else:
        fail_log = f"""회복 성공: {dice_result.is_success} | 총 회복량 = 기본 회복량 {heal_point}): {total_healing}"""
        rule(fail_log)
        logs.append(fail_log)

    new_diff = EntityDiff(state_entity_id=player_id, diff={"hp": total_healing})
    diffs.append(new_diff)
    rule(f"diffs.append({new_diff.model_dump()})")

    return {
        "diffs": diffs,
        "relations": relations,
        "is_success": dice_result.is_success,
        "logs": logs,
    }
