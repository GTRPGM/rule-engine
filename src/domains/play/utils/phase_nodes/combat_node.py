from typing import Any, Dict, List

from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityType,
    PlaySessionState,
)

from .combat_node_methods.calculate_player_power import calculate_player_power
from .combat_node_methods.determine_target_enemy import determine_target_enemy
from .combat_node_methods.get_enemy_combat_info import get_enemy_combat_info
from .combat_node_methods.handle_player_check import handle_player_check
from .combat_node_methods.process_combat_outcome import process_combat_outcome


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

    player_check_result = await handle_player_check(
        player_id, player_state, logs, state.relations
    )
    if player_check_result:
        return player_check_result

    enemy_state_ids = await determine_target_enemy(state, enemies, player_id, logs)
    combat_enemies_info: List[Dict[str, Any]] = []

    combat_enemies_info = await get_enemy_combat_info(
        enemy_state_ids, enemies, enemy_service, logs
    )

    player_combat_power = await calculate_player_power(
        state, gm_service, item_service, player_state, logs
    )

    diffs, is_success = await process_combat_outcome(
        player_id, player_combat_power, combat_enemies_info, logs
    )

    return {
        "diffs": diffs,
        "relations": state.relations,  # 관계는 전투 핸들러에서 직접 업데이트되지 않고 통과
        "is_success": is_success,
        "logs": logs,
    }
