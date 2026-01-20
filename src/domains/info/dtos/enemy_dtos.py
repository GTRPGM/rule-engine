from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from common.dtos.pagination_meta import PaginationMeta


class EnemyRequest(BaseModel):
    enemy_ids: Optional[List[int]] = Field(None, description="조회할 적 ID 리스트")
    skip: int = Field(
        0,
        ge=0,
        description="건너뛸 이전 페이지 정보들 = 페이지 * 페이지당 보여줄 행 수",
    )
    limit: int = Field(20, ge=1, le=100, description="페이지당 보여줄 정보 제한")


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
