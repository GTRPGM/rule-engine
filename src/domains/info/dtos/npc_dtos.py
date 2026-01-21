from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from common.dtos.pagination_meta import PaginationMeta


class NpcRequest(BaseModel):
    npc_ids: Optional[List[int]] = Field(None, description="조회할 NPC ID 리스트")
    skip: int = Field(
        0,
        ge=0,
        description="건너뛸 이전 페이지 정보들 = 페이지 * 페이지당 보여줄 행 수",
    )
    limit: int = Field(20, ge=1, le=100, description="페이지당 보여줄 정보 제한")


class NpcResponse(BaseModel):
    npc_id: int
    name: str
    disposition: Optional[str]
    occupation: Optional[str]
    dialogue_style: Optional[str]
    description: Optional[str]
    base_difficulty: int
    combat_description: Optional[str]
    creator: str
    created_at: datetime


class PaginatedNpcResponse(BaseModel):
    npcs: List[NpcResponse]
    meta: PaginationMeta


class NpcInventoryItem(BaseModel):
    inventory_id: int
    item_id: int
    base_price: int
    is_infinite_stock: bool


# 2. 아이템 목록을 포함한 NPC 상세 정보 DTO
class NpcDetailResponse(BaseModel):
    npc_id: int
    name: str
    disposition: Optional[str] = "중립"
    occupation: Optional[str] = None
    dialogue_style: Optional[str] = None
    description: Optional[str] = None
    base_difficulty: int = 10
    combat_description: Optional[str] = None
    created_at: datetime
    inventory_list: List[NpcInventoryItem] = Field(default_factory=list)
