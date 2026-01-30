from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ItemCategory(str, Enum):
    WEAPON = "무기"
    ARMOR = "방어구"
    TOOL = "도구"
    CONSUMABLE = "소모품"
    ETC = "기타"
    MATERIAL = "재료"
    ENHANCE = "강화"
    RELIC = "유물"

    @classmethod
    def list_values(cls):
        return [c.value for c in cls]


class ItemGrade(str, Enum):
    Common = "Common"
    Rare = "Rare"
    Epic = "Epic"
    Legendary = "Legendary"

    @classmethod
    def list_values(cls):
        return [c.value for c in cls]


class ItemCreateRequest(BaseModel):
    name: str
    type: ItemCategory
    effect_value: int = 0
    description: str | None = None
    weight: int = 1
    grade: ItemGrade
    base_price: int = 0


class EnemyCreateRequest(BaseModel):
    name: str
    base_difficulty: int
    description: str | None = None
    type: str


class EnemyDropCreateRequest(BaseModel):
    enemy_id: int
    item_id: int
    drop_rate: float
    min_quantity: int
    max_quantity: int


class NpcCreateRequest(BaseModel):
    name: str
    disposition: str
    occupation: str
    dialogue_style: str
    description: str
    base_difficulty: int
    combat_description: str


class NpcInventoryCreateRequest(BaseModel):
    npc_id: int = Field(..., description="판매 주체 NPC의 ID")
    item_id: int = Field(..., description="판매할 아이템의 ID")
    is_infinite_stock: Optional[bool] = Field(
        False, description="재고 무한 여부 (True: 무한, False: 한정)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "npc_id": 1,
                "item_id": 10,
                "is_infinite_stock": True,
            }
        }
