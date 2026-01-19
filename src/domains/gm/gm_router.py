from fastapi import APIRouter, Query

from utils.dice_util import DiceUtil

gm_router = APIRouter(prefix="/gm", tags=["GM 요청"])


@gm_router.get(
    "/action/check",
    summary="주사위 판정 실행",
    description="2d6 주사위를 굴려 플레이어의 능력치를 더한 후, 설정된 난이도와 비교하여 성공 여부를 판정합니다.",
)
async def perform_action(
    ability_val: int = Query(
        ...,
        title="플레이어 능력치",
        description="판정에 사용될 캐릭터의 기본 능력치(난폭함, 똘똘함, 영리함 등) 수치입니다.",
        ge=0,  # 0 이상의 값만 허용
        le=50,  # 최대치 제한 (예시)
        examples=[3],
    ),
    diff: int = Query(
        ...,
        title="판정 난이도",
        description="해당 행동을 성공시키기 위해 넘어야 할 목표 수치입니다. (보통 6~12 사이)",
        ge=2,
        le=30,
        examples=[10],
    ),
):
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

    return {
        "message": msg,
        "roll_result": result["roll_result"],
        "total": result["total"],
        "is_success": result["is_success"],
    }
