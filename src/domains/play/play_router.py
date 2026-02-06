from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_utils.cbv import cbv
from starlette.responses import StreamingResponse

from common.dtos.proxy_service_dto import ProxyService
from common.dtos.wrapped_response import WrappedResponse
from common.utils.get_services import (
    get_enemy_service,
    get_item_service,
    get_minigame_service,
    get_npc_service,
    get_personality_service,
    get_play_service,
    get_world_service,
)
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.info.npc_service import NpcService
from domains.info.personality_service import PersonalityService
from domains.info.world_service import WorldService
from domains.play.dtos.play_dtos import PlaySceneRequest, PlaySceneResponse
from domains.play.dtos.player_dtos import FullPlayerState
from domains.play.dtos.riddle_dtos import AnswerRequest, AnswerResponse
from domains.play.minigame_service import MinigameService
from domains.play.play_service import PlayService
from utils.logger import error
from utils.proxy_request import proxy_request

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
        except HTTPException as he:
            raise he
        except Exception as e:
            error(f"시나리오 파악 오류: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알 수 없는 오류가 발생했습니다.",
            )

    @play_router.get(
        "/player/{player_id}",
        summary="대상 플레이어의 상세 정보(상태, 보유 아이템 목록, NPC 우호도 목록)를 조회합니다.",
        response_model=WrappedResponse[FullPlayerState],
    )
    async def player(self, player_id: str):
        return await proxy_request(
            "GET",
            f"/state/player/{player_id}",
            provider=ProxyService.STATE_MANAGER,
        )

    @play_router.get(
        "/riddle/{user_id}",
        summary="새로운 수수께끼를 생성하고 스트리밍으로 반환합니다. 동시에 Redis에 정답과 초기 상태를 저장합니다.",
    )
    async def get_riddle(
        self, user_id: int, service: MinigameService = Depends(get_minigame_service)
    ):
        """
        새로운 수수께끼를 생성하고 스트리밍으로 반환합니다.
        동시에 Redis에 정답과 초기 상태를 저장합니다.
        """
        try:
            # 서비스에서 스트리밍 제너레이터 획득
            riddle_stream = await service.generate_and_save_riddle(user_id)

            return StreamingResponse(riddle_stream, media_type="text/event-stream")
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"수수께끼 생성 실패: {str(e)}")

    @play_router.get(
        "/quiz/{user_id}",
        summary="새로운 동굴탐험대 문제를 생성하고 스트리밍으로 반환합니다. 동시에 Redis에 정답과 초기 상태를 저장합니다.",
    )
    async def get_quiz(
        self,
        user_id: int,
        minigame_service: MinigameService = Depends(get_minigame_service),
        item_service: ItemService = Depends(get_item_service),
        enemy_service: EnemyService = Depends(get_enemy_service),
        npc_service: NpcService = Depends(get_npc_service),
        personality_service: PersonalityService = Depends(get_personality_service),
        world_service: WorldService = Depends(get_world_service),
    ):
        """
        새로운 동굴 탐험대 퀴즈를 생성하고 스트리밍으로 반환합니다.
        동시에 Redis에 정답과 초기 상태를 저장합니다.
        """
        try:
            # 서비스에서 스트리밍 제너레이터 획득
            what_stream = await minigame_service.generate_and_save_quiz(
                user_id,
                item_service,
                enemy_service,
                npc_service,
                personality_service,
                world_service,
            )

            return StreamingResponse(what_stream, media_type="text/event-stream")
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"문제 생성 실패: {str(e)}")

    @play_router.post(
        "/answer/{user_id}",
        summary="사용자가 입력한 수수께끼 정답을 확인합니다. 3회 실패 시 힌트를 포함하며, 남은 시간(TTL)을 반환합니다.",
        response_model=WrappedResponse[AnswerResponse],
    )
    async def submit_answer(
        self,
        user_id: int,
        request: AnswerRequest,
        service: MinigameService = Depends(get_minigame_service),
    ):
        """
        사용자가 입력한 정답을 확인합니다.
        3회 실패 시 힌트를 포함하며, 남은 시간(TTL)을 반환합니다.
        """
        try:
            feedback = await service.check_user_answer(
                user_id, request.user_guess, request.flag
            )

            if feedback.result == "error":
                raise HTTPException(status_code=404, detail=feedback.message)

            return WrappedResponse[AnswerResponse](data=feedback)
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"{'수수께끼' if request.flag == 'RIDDLE' else '퀴즈'} 답안 제출 실패: {str(e)}",
            )
