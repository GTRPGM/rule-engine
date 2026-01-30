from fastapi import APIRouter, Depends, HTTPException, Query, status

from common.dtos.wrapped_response import WrappedResponse
from common.utils.get_services import get_gm_service
from domains.gm.gm_service import GmService
from src.domains.gm.dtos.dice_check_result import DiceCheckResult

gm_router = APIRouter(prefix="/gm", tags=["GM 요청"])


# 아래 라우터는 백업용으로 존치 → 주사위만 따로 호출하는 케이스가 없으므로 엔드 포인트에서 배제
@gm_router.get(
    "/action/check",
    response_model=WrappedResponse[DiceCheckResult],
    summary="주사위 판정 실행",
    description="2d6 주사위를 굴려 플레이어의 능력치를 더한 후, 설정된 난이도와 비교해 성공 여부를 판정합니다.",
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
    gm_service: GmService = Depends(get_gm_service),
):
    """주사위 판정을 실행합니다."""
    try:
        result = await gm_service.rolling_dice(ability_val, diff)

        return {"data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"주사위 판정 실패: {str(e)}",
        )
