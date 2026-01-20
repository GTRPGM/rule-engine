from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from common.dtos.pagination_meta import PaginationMeta


class EnemyRequest(BaseModel):
    enemy_ids: Optional[List[int]] = Field(None, description="조회할 아이템 ID 리스트")
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class EnemyResponse(BaseModel):
    enemy_id: int
    name: str
    base_difficulty: int
    description: str
    type: str
    created_at: datetime


class PaginatedEnemyResponse(BaseModel):
    items: List[EnemyResponse]
    meta: PaginationMeta
