from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_utils.cbv import cbv
from starlette.responses import StreamingResponse

from common.dtos.wrapped_response import WrappedResponse
from common.utils.get_services import get_minigame_service, get_play_service
from domains.play.dtos.play_dtos import PlaySceneRequest, PlaySceneResponse
from domains.play.minigame_service import MinigameService
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

    @play_router.get("/minigame", summary="수수께끼 미니게임을 진행합니다.")
    async def get_riddle(
        self,
        minigame_service: MinigameService = Depends(get_minigame_service),
    ):
        """스트리밍 응답 반환 엔드포인트"""
        return StreamingResponse(
            minigame_service.generate_riddle(), media_type="text/event-stream"
        )

    # @play_router.post("/check-answer")
    # async def check_answer(user_id: str, user_guess: str, service: MinigameService):
    # Todo: 1. REDIS에서 해당 유저의 정답 조회
    # correct_answer = service.get_saved_answer(user_id)

    # 2. 비교 (공백 제거, 대소문자 무시 등)
    # if user_guess.strip() == correct_answer.strip():
    #     return {"result": "correct", "message": "정답입니다! 🎉"}
    # else:
    #     return {"result": "wrong", "message": "틀렸습니다. 다시 생각해보세요!"}
