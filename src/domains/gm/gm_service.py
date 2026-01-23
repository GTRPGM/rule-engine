from domains.gm.dtos.dice_check_result import DiceCheckResult
from utils.dice_util import DiceUtil


class GmService:
    def __init__(self, cursor):
        self.cursor = cursor

    async def rolling_dice(
        self,
        ability_val: int,
        diff: int,
    ) -> DiceCheckResult:
        """주사위 판정을 실행합니다."""
        result = DiceUtil.check_success(ability_val, diff)

        if result["is_critical_success"]:
            msg = "🎯 대성공! 완벽한 운이 따랐습니다."
        elif result["is_critical_fail"]:
            msg = "💀 대실패... 운명의 신이 당신을 저버렸습니다."
        elif result["is_success"]:
            msg = "✅ 성공했습니다."
        else:
            msg = "❌ 실패했습니다."

        return DiceCheckResult(
            message=msg,
            roll_result=result["roll_result"],
            total=result["total"],
            is_success=result["is_success"],
        )
