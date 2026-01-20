from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class WorldInfoKey(str, Enum):
    CONFIGS = "configs"
    ERAS = "eras"
    LOCALES = "locales"
    CHARACTERS = "characters"
    ABILITIES = "abilities"


class WorldRequest(BaseModel):
    include_keys: Optional[List[WorldInfoKey]] = Field(None)


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


class Ability(BaseModel):
    ability_id: int
    name: str
    description: str


class WorldResponse(BaseModel):
    configs: Optional[List[SysConfig]] = None
    eras: Optional[List[WorldEra]] = None
    locales: Optional[List[WorldLocale]] = None
    characters: Optional[List[Character]] = None
    abilities: Optional[List[Ability]] = None
