from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_utils.cbv import cbv

from common.dtos.wrapped_response import WrappedResponse
from common.utils.get_services import get_scenario_service
from domains.scenario.dtos.scenario_dtos import (
    EnemyCreateRequest,
    EnemyDropCreateRequest,
    ItemCreateRequest,
    NpcInventoryCreateRequest,
)
from domains.scenario.scenario_service import ScenarioService
from utils.logger import error

scenario_router = APIRouter(prefix="/scenario", tags=["시나리오 요소 생성"])


@cbv(scenario_router)
class ScenarioHandler:
    @scenario_router.post(
        "/item",
        summary="아이템 생성",
        response_model=WrappedResponse[int],
    )
    async def add_item(
        self,
        request_data: ItemCreateRequest,
        scenario_service: ScenarioService = Depends(get_scenario_service),
    ):
        try:
            new_id = await scenario_service.add_item(request_data)
            return {"data": new_id, "message": "아이템이 생성되었습니다."}

        except HTTPException as he:
            raise he
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            error(f"아이템 생성 실패: {e}")  # 서버 로그 기록
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"아이템 생성 실패: {str(e)}",
            )

    @scenario_router.post(
        "/enemy",
        summary="적 생성",
        response_model=WrappedResponse[int],
    )
    async def add_enemy(
        self,
        request_data: EnemyCreateRequest,
        scenario_service: ScenarioService = Depends(get_scenario_service),
    ):
        try:
            new_id = await scenario_service.add_enemy(request_data)
            return {"data": new_id, "message": "적이 생성되었습니다."}

        except HTTPException as he:
            raise he
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            error(f"적 생성 오류: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"적 생성 실패: {str(e)}",
            )

    @scenario_router.post(
        "/enemy-drop",
        summary="적 드랍 아이템 생성",
        response_model=WrappedResponse[int],
    )
    async def add_enemy_drop(
        self,
        request_data: EnemyDropCreateRequest,
        scenario_service: ScenarioService = Depends(get_scenario_service),
    ):
        try:
            new_id = await scenario_service.add_enemy_drop(request_data)
            return {"data": new_id, "message": "적 드랍 아이템 정보가 생성되었습니다."}

        except HTTPException as he:
            raise he
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            error(f"적 드롭 아이템 생성 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"적 드랍 아이템 생성 실패: {str(e)}",
            )

    @scenario_router.post(
        "/npc",
        summary="NPC 생성",
        response_model=WrappedResponse[int],
    )
    async def add_npc(
        self,
        request_data: EnemyCreateRequest,
        scenario_service: ScenarioService = Depends(get_scenario_service),
    ):
        try:
            new_id = await scenario_service.add_npc(request_data)
            return {"data": new_id, "message": "NPC가 생성되었습니다."}

        except HTTPException as he:
            raise he
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            error(f"NPC 생성 실패: {e}")  # 서버 로그 기록
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"NPC 생성 실패: {str(e)}",
            )

    @scenario_router.post(
        "/npc-inventory",
        summary="NPC 인벤토리 생성",
        response_model=WrappedResponse[int],
    )
    async def add_npc_inventory(
        self,
        request_data: NpcInventoryCreateRequest,
        scenario_service: ScenarioService = Depends(get_scenario_service),
    ):
        try:
            new_id = await scenario_service.add_npc_inventory(request_data)
            return {"data": new_id, "message": "NPC 인벤토리가 생성되었습니다."}

        except HTTPException as he:
            raise he
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            error(f"NPC 인벤토리 생성 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"NPC 인벤토리 생성 실패: {str(e)}",
            )
