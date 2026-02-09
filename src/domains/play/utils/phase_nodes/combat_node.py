import re
from typing import Any, Dict, List, Optional

from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityDiff,
    EntityType,
    PlaySessionState,
    RelationType,
)
from domains.play.dtos.player_dtos import ItemBase
from utils.logger import rule


def _try_parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw or not raw.isdigit():
        return None
    return int(raw)


def _is_combat_item_type(item_type: Optional[str]) -> bool:
    if not item_type:
        return False
    normalized = str(item_type).strip().lower()
    return normalized in {"무기", "방어구", "equipment", "weapon", "armor"}


def _normalize_for_match(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", str(value).lower())


def _resolve_target_enemy_state_id(
    requested_target: str, enemies: List[Any]
) -> Optional[str]:
    target_raw = str(requested_target or "").strip()
    if not target_raw:
        return None

    target_lower = target_raw.lower()
    target_norm = _normalize_for_match(target_raw)
    if not target_norm:
        return None

    best_state_id: Optional[str] = None
    best_score = 0
    for enemy in enemies:
        state_id = str(getattr(enemy, "state_entity_id", "") or "").strip()
        if not state_id:
            continue
        entity_name = str(getattr(enemy, "entity_name", "") or "").strip()
        aliases = {state_id, entity_name}
        aliases = {a for a in aliases if a}
        if not aliases:
            continue

        candidate_score = 0
        for alias in aliases:
            alias_lower = alias.lower()
            alias_norm = _normalize_for_match(alias)
            if not alias_norm:
                continue

            score = 0
            if target_lower == alias_lower or target_norm == alias_norm:
                score = max(score, 120 + len(alias_norm))
            if alias_lower in target_lower:
                score = max(score, 90 + len(alias_lower))
            if alias_norm in target_norm:
                score = max(score, 80 + len(alias_norm))
            candidate_score = max(candidate_score, score)

        if candidate_score > best_score:
            best_score = candidate_score
            best_state_id = state_id

    return best_state_id if best_score > 0 else None


def _extract_effect_value(meta: Dict[str, Any]) -> int:
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


async def _calculate_player_combat_item_effect(
    player_items: List[ItemBase], item_service: ItemService, logs: List[str]
) -> int:
    numeric_item_ids: List[int] = []
    for item in player_items:
        parsed = _try_parse_int(item.item_id)
        if parsed is not None:
            numeric_item_ids.append(parsed)

    effect_sum = 0
    resolved_numeric_ids: set[str] = set()
    if numeric_item_ids:
        items, _ = await item_service.get_items(
            item_ids=list(set(numeric_item_ids)), skip=0, limit=100
        )
        for db_item in items:
            if _is_combat_item_type(db_item.get("type")):
                effect_sum += int(db_item.get("effect_value") or 0)
            db_item_id = db_item.get("item_id")
            if db_item_id is not None:
                resolved_numeric_ids.add(str(db_item_id))

    # scenario_item_id(문자열) 기반 인벤토리도 처리되도록 로컬 메타를 fallback으로 사용.
    for item in player_items:
        if item.item_id in resolved_numeric_ids:
            continue
        if not _is_combat_item_type(item.item_type):
            continue
        effect_sum += _extract_effect_value(item.meta)

    if effect_sum > 0:
        logs.append(f"전투 보정치(아이템): {effect_sum}")
        rule(f"전투 보정치(아이템): {effect_sum}")

    return effect_sum


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
        rule("전투 페이즈: 플레이어 정보를 찾을 수 없습니다.")
        return {
            "diffs": state.diffs,
            "relations": state.relations,
            "is_success": False,
            "logs": logs,
        }

    # 적 상세정보 조회
    combat_enemies_info = []
    hostile_enemy_state_ids = {
        (
            rel.effect_entity_id
            if rel.cause_entity_id == player_id
            else rel.cause_entity_id
        )
        for rel in state.request.relations
        if rel.type == RelationType.HOSTILE
        and (rel.cause_entity_id == player_id or rel.effect_entity_id == player_id)
    }

    requested_target = str(getattr(state.request, "target", "") or "").strip()
    resolved_target_state_id = _resolve_target_enemy_state_id(requested_target, enemies)

    if resolved_target_state_id:
        enemy_state_ids = {resolved_target_state_id}
        target_log = f"요청 target='{requested_target}' -> 전투 대상 {resolved_target_state_id}로 고정."
        logs.append(target_log)
        rule(target_log)
    elif hostile_enemy_state_ids:
        first_id = next(iter(hostile_enemy_state_ids), None)
        enemy_state_ids = {first_id}

        hostile_target_log = (
            f"적대 관계 목록 중 첫 번째 대상({first_id})을 전투 대상으로 설정합니다."
        )
        logs.append(hostile_target_log)
        rule(hostile_target_log)
    else:
        if enemies:
            target_enemy = enemies[0]
            enemy_state_ids = {target_enemy.state_entity_id}

            no_enemies_log = f"적대 관계 정보가 없어 목록의 첫 번째 적({target_enemy.state_entity_id})을 대상으로 설정합니다."
            logs.append(no_enemies_log)
            rule(no_enemies_log)
        else:
            enemy_state_ids = set()
            no_enemies_log = "전투 가능한 적이 목록에 없습니다."
            logs.append(no_enemies_log)
            rule(no_enemies_log)

    enemy_id_map = {
        e.state_entity_id: e.entity_id
        for e in enemies
        if e.state_entity_id in enemy_state_ids and e.entity_id is not None
    }

    enemy_rdb_ids = list(set([e.entity_id for e in enemies if e.entity_id is not None]))
    enemies_data, _ = await enemy_service.get_enemies(
        enemy_ids=enemy_rdb_ids, skip=0, limit=100
    )
    enemy_details_map = {e["enemy_id"]: e for e in enemies_data}

    # 정책: 한 번에 대상 하나만 공격 | 광역기 없음
    # 나중에 정책이 바뀔 가능성에 대비해 반복문 형태 유지
    for state_id in enemy_state_ids:
        rdb_id = enemy_id_map.get(state_id)
        base_difficulty = None
        if rdb_id is not None:
            enemy_data = enemy_details_map.get(rdb_id)
            if enemy_data and enemy_data.get("base_difficulty") is not None:
                base_difficulty = int(enemy_data["base_difficulty"])

        if base_difficulty is None:
            # 상세 조회 실패 시에도 전투 처리를 중단하지 않기 위한 기본 난이도
            base_difficulty = 6
            no_enemy_detail_log = f"적 상세정보 누락(state_id={state_id}, rdb_id={rdb_id})으로 기본 난이도 6을 사용합니다."
            logs.append(no_enemy_detail_log)
            rule(no_enemy_detail_log)

        combat_enemies_info.append(
            {
                "rdb_id": rdb_id,
                "state_id": state_id,
                "base_difficulty": base_difficulty,
            }
        )

    # 플레이어 전투력 계산
    combat_logs: List[str] = []
    dice = await gm_service.rolling_dice(2, 6)
    dice_result_log = f"전투 시도... {dice.message}{' | 잭팟!!' if dice.is_critical_success else ''} | 굴림값 {dice.roll_result} + 능력보정치 {dice.ability_score} = 총합 {dice.total}"
    rule(dice_result_log)
    combat_logs.append(dice_result_log)

    combat_items_effect = await _calculate_player_combat_item_effect(
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
            rule(f"전투 승리! 적에게 {power_gap}의 데미지를 입혔습니다.")

        elif power_gap < 0:
            is_success = False
            new_diff = EntityDiff(
                state_entity_id=player_id,
                diff={"hp": power_gap},
            )
            diffs.append(new_diff)
            logs.append(f"전투 패배... 플레이어가 {-power_gap}의 데미지를 입었습니다.")
            rule(f"전투 패배... 플레이어가 {-power_gap}의 데미지를 입었습니다.")
        else:
            logs.append("막상막하의 대결이었습니다!")
            rule("막상막하의 대결이었습니다!")

    return {
        "diffs": diffs,
        "relations": state.relations,  # 관계는 전투 핸들러에서 직접 업데이트되지 않고 통과
        "is_success": is_success,
        "logs": logs,
    }
