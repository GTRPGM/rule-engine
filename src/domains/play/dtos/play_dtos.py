from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class PhaseType(str, Enum):
    EXPLORATION = "탐험"
    COMBAT = "전투"
    DIALOGUE = "대화"
    NEGO = "흥정"
    REST = "휴식"
    RECOVERY = "회복"
    UNKNOWN = "알 수 없음"


class RelationType(str, Enum):
    HOSTILE = "적대적"
    LITTLE_HOSTILE = "약간 적대적"
    NEUTRAL = "중립적"
    LITTLE_FRIENDLY = "약간 우호적"
    FRIENDLY = "우호적"
    OWNERSHIP = "소유"
    CONSUME = "소비"
    SELF = "본인"


# 아직 구체화되지 않음 - 상상 자료형
class ActionType(str, Enum):
    ATTACK = "공격"
    DAMAGED = "피해"
    DEFENCE = "방어"
    AVOID = "회피"
    DISCOVER = "발견"
    DEAD = "사망"
    ACQUIRE = "습득"
    THROW = "버림"


class SceneAnalysis(BaseModel):
    phase_type: PhaseType = Field(description="현재 시나리오의 플레이 유형")
    reason: str = Field(description="그렇게 판단한 이유 요약")
    confidence: float = Field(description="판단 확신도 (0.0 ~ 1.0)")


class PlaySceneData(BaseModel):
    story: str
    who: str
    target: str
    where: str


class EntityType(Enum):
    PLAYER = "player"
    NPC = "npc"
    ENEMY = "enemy"
    ITEM = "item"
    OBJECT = "object"  # 상자 등 상호작용 가능한 대상 물체


class EntityUnit(BaseModel):
    state_entity_id: str  # 객체 식별 번호
    entity_id: Optional[int] = (
        None  # RDB 객체 식별 번호 - 플레이어나 사물 타입은 존재 안 함
    )
    quantity: Optional[int] = Field(description="아이템 수량", default=None)
    phase_id: int
    entity_name: str
    entity_type: EntityType


class EntityDiff(BaseModel):
    state_entity_id: str
    diff: Any  # - 플레이어 변동치, 보유 아이템 변동치 - 가변적
    #   { "state_entity_id": "player_id", "hp": -10 },
    #   { "state_entity_id": "UUID", "quantity": -1 },


class UpdateRelation(BaseModel):
    cause_entity_id: str = Field(description="원인")
    effect_entity_id: str = Field(description="결과")
    type: RelationType
    affinity_score: Optional[int] = Field(default=None, description="우호도 점수")
    quantity: Optional[int] = Field(default=None, description="수량")


class PhaseUpdate(BaseModel):
    diffs: List[EntityDiff] = Field(
        default_factory=list, description="엔티티 변동 내역"
    )
    relations: List[UpdateRelation] = Field(
        default_factory=list, description="관계 변동 내역"
    )


class PlaySceneRequest(BaseModel):
    session_id: str
    scenario_id: str
    locale_id: int
    entities: List[EntityUnit]
    relations: List[UpdateRelation]
    story: str


class PlaySceneResponse(BaseModel):
    session_id: str
    scenario_id: str
    phase_type: PhaseType  # 룰 엔진이 추론한 페이즈 유형
    reason: str  # 페이즈 유형 판정 이유
    success: bool  # 룰 엔진 주사위 행동 판정 결과 → 시나리오 참고용(무시당할 수 있음)
    suggested: PhaseUpdate = Field(default_factory=dict, description="제안된 판정 결과")
    # Todo: 보정 들어간 주사위 판정 최대 / 최소치 산정해 반환하기
    value_range: Optional[int] = (
        None  # 룰 엔진 주사위 판정 기준(2d6 or 1d6) → 최대 / 최소
    )
    logs: Optional[List[str]] = None


class HandlerUpdatePhase(BaseModel):
    update: PhaseUpdate
    is_success: bool
    logs: Optional[List[str]] = None
