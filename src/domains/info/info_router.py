from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi_utils.cbv import cbv

from common.dtos.wrapped_response import WrappedResponse
from common.utils.get_services import (
    get_enemy_service,
    get_item_service,
    get_personality_service,
    get_world_service,
)
from domains.info.dtos.enemy_dtos import EnemyRequest, PaginatedEnemyResponse
from domains.info.dtos.personality_dtos import (
    PaginatedPersonalityResponse,
    PersonalityRequest,
)
from domains.info.dtos.world_dtos import WorldInfoKey, WorldResponse
from domains.info.enemy_service import EnemyService
from domains.info.personality_service import PersonalityService
from domains.info.world_service import WorldService
from src.domains.info.dtos.item_dtos import ItemRequest, PaginatedItemResponse
from src.domains.info.item_service import ItemService

info_router = APIRouter(prefix="/info", tags=["게임 정보 조회"])


@cbv(info_router)
class InfoHandler:
    @info_router.post(
        "/items",
        summary="아이템 조회",
        response_model=WrappedResponse[PaginatedItemResponse],
    )
    async def read_items(
        self,
        request_data: ItemRequest,
        item_service: ItemService = Depends(get_item_service),
    ):
        # 서비스 계층 호출 (실제 구현 시 의존성 주입된 인스턴스 사용)
        items, meta = await item_service.get_items(
            request_data.item_ids, request_data.skip, request_data.limit
        )

        return {"data": {"items": items, "meta": meta}}

    @info_router.post(
        "/enemies",
        summary="적 정보 조회",
        response_model=WrappedResponse[PaginatedEnemyResponse],
    )
    async def read_enemies(
        self,
        request_data: EnemyRequest,
        enemy_service: EnemyService = Depends(get_enemy_service),
    ):
        enemies, meta = await enemy_service.get_enemies(
            request_data.enemy_ids, request_data.skip, request_data.limit
        )

        return {"data": {"enemies": enemies, "meta": meta}}

    @info_router.post(
        "/personalities",
        summary="NPC 생성 시 필요한 성격 정보를 조회합니다.",
        response_model=WrappedResponse[PaginatedPersonalityResponse],
    )
    async def read_personalities(
        self,
        request_data: PersonalityRequest,
        personality_service: PersonalityService = Depends(get_personality_service),
    ):
        personalities, meta = await personality_service.get_personalities(
            request_data.personality_ids, request_data.skip, request_data.limit
        )

        return {"data": {"personalities": personalities, "meta": meta}}

    @info_router.get(
        "/world",
        summary="시나리오 생성 시 필요한 시스템 설정·공간적·시간적 배경·캐릭터 정보를 조회합니다.",
        response_model=WrappedResponse[WorldResponse],
    )
    async def read_world(
        self,
        include_keys: Optional[List[WorldInfoKey]] = Query(
            None,
            description=(
                "조회할 정보 키 리스트입니다. (예: ?include_keys=configs&include_keys=eras)<br>"
                "선택하지 않으면 전체 정보를 반환합니다.<br>"
                "• **configs**: 시스템 설정<br>• **eras**: 시대<br>• **locales**: 장소<br>• **characters**: 캐릭터"
            ),
        ),
        world_service: WorldService = Depends(get_world_service),
    ):
        world_data = await world_service.get_world(include_keys)
        return {"data": world_data}
