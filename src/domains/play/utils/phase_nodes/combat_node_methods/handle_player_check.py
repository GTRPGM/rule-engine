from typing import Any, Dict, List, Optional

from utils.logger import rule


async def handle_player_check(
    player_id: Optional[str],
    player_state: Any,
    logs: List[str],
    state_relations: Any,
) -> Optional[Dict[str, Any]]:
    """
    플레이어 정보를 확인하고, 유효하지 않으면 오류를 로깅하고 early-exit 딕셔너리를 반환합니다.
    """
    if not player_id or not player_state:
        logs.append("전투 페이즈: 플레이어 정보를 찾을 수 없습니다.")
        rule("전투 페이즈: 플레이어 정보를 찾을 수 없습니다.")
        return {
            "diffs": [],
            "relations": state_relations,
            "is_success": False,
            "logs": logs,
        }
    return None
