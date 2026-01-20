from typing import List, Optional
from datetime import datetime

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
    created_at: datetime


class PaginatedNpcResponse(BaseModel):
    npcs: List[NpcResponse]
    meta: PaginationMeta
