from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class PlayType(str, Enum):
    BATTLE = "전투"
    NEGOTIATE = "협상"
    EXPLORE = "탐험"
    UNKNOWN = "알 수 없음"


class SceneAnalysis(BaseModel):
    play_type: PlayType = Field(description="현재 시나리오의 플레이 유형")
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


class PlaySceneUpdate(BaseModel):
    entity_id: int
    entity_attribute: Any
    entity_relation: Optional[EntityRelation] = None


class FeedbackResponse(BaseModel):
    message: str
    requirements: Optional[List[str]] = None


class PlaySceneResponse(BaseModel):
    session_id: int
    scenario_id: int
    update: List[Optional[PlaySceneUpdate]]
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
