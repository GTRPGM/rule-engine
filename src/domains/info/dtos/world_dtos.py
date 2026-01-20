from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class WorldInfoKey(str, Enum):
    CONFIGS = "configs"
    ERAS = "eras"
    LOCALES = "locales"
    CHARACTERS = "characters"


class WorldRequest(BaseModel):
    # 선택적으로 가져올 키 리스트 (예: ["eras", "locales"])
    # None이거나 빈 배열이면 전체 조회로 간주
    include_keys: Optional[List[WorldInfoKey]] = Field(
        None,
        description=(
            "조회할 정보 키 리스트입니다. 선택하지 않으면 전체 정보를 반환합니다.<br>"
            "• **configs**: 게임 시스템 설정 값 (난이도, 배율 등)<br>"
            "• **eras**: 시대적 배경 및 스테이터스 보정치<br>"
            "• **locales**: 방문 가능한 장소 및 위험도<br>"
            "• **characters**: 선택 가능한 초기 캐릭터 클래스 정보"
        ),
        # Swagger 예시 값 설정
        examples=[["configs", "eras", "locales", "characters"]],
    )


class SysConfig(BaseModel):
    config_key: str
    config_value: int
    description: str


class WorldEra(BaseModel):
    era_id: int
    era_name: str
    stat_modifier: float
    description: str
    created_at: datetime


class WorldLocale(BaseModel):
    locale_id: int
    name: str
    theme: str
    danger_min: int
    danger_max: int
    description: str
    created_at: datetime


class Character(BaseModel):
    character_id: int
    state: str
    dice_roll: int
    class_name: str
    ability_id: int | None = None
    stat_bonus: int
    starting_item_id: int | None = None


class WorldResponse(BaseModel):
    configs: Optional[List[SysConfig]] = None
    eras: Optional[List[WorldEra]] = None
    locales: Optional[List[WorldLocale]] = None
    characters: Optional[List[Character]] = None
