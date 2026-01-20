from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from common.dtos.wrapped_response import WrappedResponse
from common.utils.get_services import get_item_service
from src.domains.info.dtos.item_dtos import ItemRequest, PaginatedItemResponse
from src.domains.info.item_service import ItemService

info_router = APIRouter(prefix="/info", tags=["게임 정보 조회"])


@cbv(info_router)
class InfoHandler:
    @info_router.post(
        "/items",
        summary="아이템 목록 조회",
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
