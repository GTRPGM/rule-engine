import re
from typing import Any, List, Optional, Set

from domains.play.dtos.play_dtos import PlaySessionState, RelationType
from utils.logger import rule


def normalize_for_match(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", str(value).lower())


def resolve_target_enemy_state_id(
    requested_target: str, enemies: List[Any]
) -> Optional[str]:
    target_raw = str(requested_target or "").strip()
    if not target_raw:
        return None

    target_lower = target_raw.lower()
    target_norm = normalize_for_match(target_raw)
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
            alias_norm = normalize_for_match(alias)
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


async def determine_target_enemy(
    state: PlaySessionState, enemies: List[Any], player_id: str, logs: List[str]
) -> Set[str]:
    """
    요청된 대상 또는 적대 관계를 기반으로 전투 대상을 결정합니다.
    """
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
    resolved_target_state_id = resolve_target_enemy_state_id(requested_target, enemies)

    enemy_state_ids: Set[str] = set()

    if resolved_target_state_id:
        enemy_state_ids = {resolved_target_state_id}
        target_log = f"요청 target='{requested_target}' -> 전투 대상 {resolved_target_state_id}로 고정."
        logs.append(target_log)
        rule(target_log)
    elif hostile_enemy_state_ids:
        first_id = next(iter(hostile_enemy_state_ids), None)
        if first_id:
            enemy_state_ids = {first_id}
            hostile_target_log = f"적대 관계 목록 중 첫 번째 대상({first_id})을 전투 대상으로 설정합니다."
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
            no_enemies_log = "전투 가능한 적이 목록에 없습니다."
            logs.append(no_enemies_log)
            rule(no_enemies_log)

    return enemy_state_ids
