from typing import Any, Dict, List

from domains.play.dtos.play_dtos import EntityDiff
from utils.logger import rule


async def process_combat_outcome(
    player_id: str,
    player_combat_power: int,
    combat_enemies_info: List[Dict[str, Any]],
    logs: List[str],
) -> tuple[List[EntityDiff], bool]:
    """
    피해를 계산하고, EntityDiff 객체를 생성하고, 전투 성공 여부를 결정합니다.
    """
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

    return diffs, is_success
