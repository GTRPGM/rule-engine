from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from common.dtos.pagination_meta import PaginationMeta


class ItemRequest(BaseModel):
    item_ids: Optional[List[int]] = Field(None, description="조회할 아이템 ID 리스트")
    skip: int = Field(
        0,
        ge=0,
        description="건너뛸 이전 페이지 정보들 = 페이지 * 페이지당 보여줄 행 수",
    )
    limit: int = Field(20, ge=1, le=100, description="페이지당 보여줄 정보 제한")


class ItemResponse(BaseModel):
    item_id: int
    name: str
    type: str
    effect_value: int
    description: Optional[str]
    weight: int
    grade: Optional[str]
    base_price: int
    creator: str
    created_at: datetime


class PaginatedItemResponse(BaseModel):
    items: List[ItemResponse]
    meta: PaginationMeta
