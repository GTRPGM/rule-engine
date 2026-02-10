from typing import Any, Dict, List

from domains.info.enemy_service import EnemyService
from utils.logger import rule


async def get_enemy_combat_info(
    enemy_state_ids: set[str],
    enemies: List[Any],
    enemy_service: EnemyService,
    logs: List[str],
) -> List[Dict[str, Any]]:
    """
    적 상세정보를 조회하고 각 적의 기본 난이도를 결정합니다.
    """
    combat_enemies_info: List[Dict[str, Any]] = []

    if not enemy_state_ids:
        return combat_enemies_info

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

    for state_id in enemy_state_ids:
        rdb_id = enemy_id_map.get(state_id)
        base_difficulty = None
        if rdb_id is not None:
            enemy_data = enemy_details_map.get(rdb_id)
            if enemy_data and enemy_data.get("base_difficulty") is not None:
                base_difficulty = int(enemy_data["base_difficulty"])

        if base_difficulty is None:
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
    return combat_enemies_info
