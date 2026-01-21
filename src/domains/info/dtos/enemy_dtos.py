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
    creator: str
    created_at: datetime


class PaginatedEnemyResponse(BaseModel):
    enemies: List[EnemyResponse]
    meta: PaginationMeta


class EnemyDropDetail(BaseModel):
    drop_id: int = Field(..., description="드롭 규칙 고유 ID")
    item_id: int = Field(..., description="아이템 ID")
    item_name: str = Field(..., description="아이템 이름")
    item_type: Optional[str] = Field(..., description="아이템 분류 (무기, 소모품 등)")
    drop_rate: float = Field(..., description="드롭 확률 (%)")
    min_quantity: int = Field(..., description="최소 드롭 수량")
    max_quantity: int = Field(..., description="최대 드롭 수량")
    grade: Optional[str] = Field(None, description="아이템 등급")


class EnemyDetailResponse(BaseModel):
    enemy_id: int = Field(..., description="적 고유 식별자")
    name: str = Field(..., description="적 이름")
    base_difficulty: int = Field(..., description="전투 난이도 (HP)")
    description: Optional[str] = Field(None, description="적 상세 묘사")
    type: Optional[str] = Field(None, description="적 유형 (기계, 정령 등)")
    created_at: datetime = Field(..., description="생성 일시")
    drops: List[EnemyDropDetail] = Field(
        default_factory=list, description="드롭 가능한 아이템 목록"
    )

    class Config:
        # DB 조회 결과(dict)를 Pydantic 모델로 자동 변환하기 위한 설정
        from_attributes = True
