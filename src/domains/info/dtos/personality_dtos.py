from typing import List, Optional

from pydantic import BaseModel, Field

from common.dtos.pagination_meta import PaginationMeta


class PersonalityRequest(BaseModel):
    personality_ids: Optional[List[str]] = Field(
        None, description="조회할 성격 ID 리스트"
    )
    skip: int = Field(
        0,
        ge=0,
        description="건너뛸 이전 페이지 정보들 = 페이지 * 페이지당 보여줄 행 수",
    )
    limit: int = Field(20, ge=1, le=100, description="페이지당 보여줄 정보 제한")


class PersonalityResponse(BaseModel):
    id: str
    category: str
    label: str
    description: Optional[str] = None
    opposite: Optional[List[str]] = None


class PaginatedPersonalityResponse(BaseModel):
    personalities: List[PersonalityResponse]
    meta: PaginationMeta
