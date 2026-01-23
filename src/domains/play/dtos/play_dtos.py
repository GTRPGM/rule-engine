from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class PhaseType(str, Enum):
    EXPLORATION = "탐험"
    COMBAT = "전투"
    DIALOGUE = "대화"
    REST = "휴식"
    UNKNOWN = "알 수 없음"


# 아직 구체화되지 않음 - 상상 자료형
class RelationType(str, Enum):
    ATTACK = "공격"
    DAMAGED = "피해"
    DEFENCE = "방어"
    AVOID = "회피"
    DISCOVER = "발견"
    DEAD = "사망"
    ACQUIRE = "습득"
    THROW = "버림"


class SceneAnalysis(BaseModel):
    play_type: PhaseType = Field(description="현재 시나리오의 플레이 유형")
    reason: str = Field(description="그렇게 판단한 이유 요약")
    confidence: float = Field(description="판단 확신도 (0.0 ~ 1.0)")


class PlaySceneData(BaseModel):
    story: str
    who: str
    target: str
    where: str


class PlaySceneRequest(BaseModel):
    session_id: int
    scenario_id: int
    data: PlaySceneData


class EntityRelation(BaseModel):
    target_entity_id: int
    update_relation: str
    target_entity_attribute: Optional[Any] = None


class PhaseUpdate(BaseModel):
    entity_id: int
    entity_attribute: Optional[Any] = None
    entity_relation: Optional[EntityRelation] = None  # 아직 구체화되지 않음


class FeedbackResponse(BaseModel):
    play_type: PhaseType
    reason: str
    requirements: Optional[List[str]] = None


class PlaySceneResponse(BaseModel):
    session_id: int
    scenario_id: int
    update: List[Optional[PhaseUpdate]]
    feedback: Optional[FeedbackResponse] = None

    # {
    #     "session_id": "",
    #     "scenario_id": "",
    #     "update": [
    #         {
    #             "entity_id": "",
    #             "entity_attribute": {
    #                 "hp": -1
    #             },
    #             "entity_relation": {
    #                 "target_entity_id": " ",
    #                 "update_relation": " "
    #             }
    #         }
    #     ]
    # }
