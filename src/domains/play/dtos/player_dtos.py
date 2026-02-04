from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    """아이템의 기본 스키마"""

    item_id: str = Field(
        ...,
        description="아이템 고유 식별자 (마스터 데이터 ID)",
        json_schema_extra={"example": "ITEM_POTION_001"},
    )
    name: str = Field(..., description="아이템 이름")
    description: Optional[str] = Field("", description="아이템 설명")
    item_type: str = Field(
        ...,
        description="아이템 분류 (예: consumable, equipment, material, quest)",
        json_schema_extra={"example": "consumable"},
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="아이템의 세부 속성 (공격력, 회복량, 무게 등)",
        json_schema_extra={"example": {"heal_amount": 20, "weight": 0.5}},
    )
    is_stackable: bool = Field(default=True, description="중첩 가능 여부")


class PlayerStateResponse(BaseModel):
    hp: int
    gold: int
    items: List[ItemBase]


class NPCRelation(BaseModel):
    npc_id: Union[str, UUID]
    npc_name: Optional[str] = None
    affinity_score: int
    model_config = ConfigDict(from_attributes=True)


class FullPlayerState(BaseModel):
    player: PlayerStateResponse
    player_npc_relations: List[NPCRelation] = []
