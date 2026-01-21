from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_utils.cbv import cbv

from common.dtos.wrapped_response import WrappedResponse
from common.utils.get_services import get_play_service
from domains.play.dtos.play_dtos import PlaySceneRequest, PlaySceneResponse
from domains.play.play_service import PlayService

play_router = APIRouter(prefix="/play", tags=["게임 플레이"])


@cbv(play_router)
class PlayRouter:
    @play_router.post(
        "/scenario",
        summary="GM의 시나리오를 파악하고 결과를 반환해 피드백 또는 상태 업데이트를 요청합니다.",
        response_model=WrappedResponse[PlaySceneResponse],
    )
    async def play_scene(
        self,
        request: PlaySceneRequest,
        play_service: PlayService = Depends(get_play_service),
    ):
        try:
            result = await play_service.play_scene(request)
            return {"data": result, "message": "룰 판정 결과를 반환합니다."}
        except Exception as e:
            print(f"Item Creation Error: {e}")  # 서버 로그 기록
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알 수 없는 오류가 발생했습니다.",
            )
