from typing import Any, Dict

from domains.gm.gm_service import GmService
from domains.play.dtos.play_dtos import PlaySessionState
from utils.logger import rule


async def unknown_node(state: PlaySessionState) -> Dict[str, Any]:
    logs = state.logs[:]
    diffs = state.diffs[:]
    relations = state.relations[:]

    gm_service: GmService = state.gm_service

    dice = await gm_service.rolling_dice(2, 6)
    dice_result_log = f"이해할 수 없는 행동... {dice.message}{' | 잭팟!!' if dice.is_critical_success else ''} | 굴림값 {dice.roll_result} + 능력보정치 {dice.ability_score} = 총합 {dice.total}"
    rule(dice_result_log)
    logs.append(dice_result_log)

    return {
        "diffs": diffs,
        "relations": relations,
        "is_success": dice.is_success,
        "logs": logs,
    }
