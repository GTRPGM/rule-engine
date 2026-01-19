import random
from typing import Any, Dict


class DiceUtil:
    @staticmethod
    def roll_2d6() -> int:
        """육면체 주사위 2개를 굴려 합계를 반환합니다."""
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        return die1 + die2

    @staticmethod
    def check_success(ability_score: int, difficulty: int) -> Dict[str, Any]:
        """
        성공 여부를 판정하고 상세 결과를 반환합니다.
        공식: 2d6 합계 + 능력치 >= 난이도
        """
        roll_val = DiceUtil.roll_2d6()
        total = roll_val + ability_score
        is_success = total >= difficulty

        return {
            "roll_result": roll_val,
            "ability_score": ability_score,
            "total": total,
            "difficulty": difficulty,
            "is_success": is_success,
            "is_critical_success": roll_val == 12,
            "is_critical_fail": roll_val == 2,
        }
