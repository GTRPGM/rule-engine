from typing import Any, Dict, List, Optional

from domains.gm.gm_service import GmService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import PlaySessionState
from domains.play.dtos.player_dtos import ItemBase
from utils.logger import rule


def try_parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw or not raw.isdigit():
        return None
    return int(raw)


def is_combat_item_type(item_type: Optional[str]) -> bool:
    if not item_type:
        return False
    normalized = str(item_type).strip().lower()
    return normalized in {"무기", "방어구", "equipment", "weapon", "armor"}


def extract_effect_value(meta: Dict[str, Any]) -> int:
    if not isinstance(meta, dict):
        return 0
    for key in (
        "effect_value",
        "attack_bonus",
        "defense_bonus",
        "attack",
        "defense",
        "power",
    ):
        value = meta.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


async def calculate_player_combat_item_effect(
    player_items: List[ItemBase], item_service: ItemService, logs: List[str]
) -> int:
    numeric_item_ids: List[int] = []
    for item in player_items:
        parsed = try_parse_int(item.item_id)
        if parsed is not None:
            numeric_item_ids.append(parsed)

    effect_sum = 0
    resolved_numeric_ids: set[str] = set()
    if numeric_item_ids:
        items, _ = await item_service.get_items(
            item_ids=list(set(numeric_item_ids)), skip=0, limit=100
        )
        for db_item in items:
            if is_combat_item_type(db_item.get("type")):
                effect_sum += int(db_item.get("effect_value") or 0)
            db_item_id = db_item.get("item_id")
            if db_item_id is not None:
                resolved_numeric_ids.add(str(db_item_id))

    # scenario_item_id(문자열) 기반 인벤토리도 처리되도록 로컬 메타를 fallback으로 사용.
    for item in player_items:
        if item.item_id in resolved_numeric_ids:
            continue
        if not is_combat_item_type(item.item_type):
            continue
        effect_sum += extract_effect_value(item.meta)

    if effect_sum > 0:
        logs.append(f"전투 보정치(아이템): {effect_sum}")
        rule(f"전투 보정치(아이템): {effect_sum}")

    return effect_sum


async def calculate_player_power(
    state: PlaySessionState,
    gm_service: GmService,
    item_service: ItemService,
    player_state: Any,
    logs: List[str],
) -> int:
    """
    플레이어의 총 전투력을 계산합니다.
    """
    combat_logs: List[str] = []
    dice = await gm_service.rolling_dice(2, 6)
    dice_result_log = f"전투 시도... {dice.message}{' | 잭팟!!' if dice.is_critical_success else ''} | 굴림값 {dice.roll_result} + 능력보정치 {dice.ability_score} = 총합 {dice.total}"
    rule(dice_result_log)
    combat_logs.append(dice_result_log)

    combat_items_effect = await calculate_player_combat_item_effect(
        player_state.player.items, item_service, logs
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

    return player_combat_power
