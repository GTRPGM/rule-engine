from abc import ABC, abstractmethod
from typing import List

from domains.gm.dtos.dice_check_result import DiceCheckResult
from domains.play.dtos.play_dtos import (
    EntityDiff,
    PhaseUpdate,
    PlaySceneRequest,
    RelationType,
    SceneAnalysis,
    UpdateRelation,
)


class PhaseHandler(ABC):
    @abstractmethod
    async def handle(
        self, request: PlaySceneRequest, analysis: SceneAnalysis, dice: DiceCheckResult
    ) -> PhaseUpdate:
        """각 페이즈에 맞는 로직을 수행하고 변화량(diffs, relations)을 반환합니다."""
        pass


class CombatHandler(PhaseHandler):
    async def handle(
        self, request: PlaySceneRequest, analysis: SceneAnalysis, dice: DiceCheckResult
    ) -> PhaseUpdate:
        # 전투 관련 주사위 룰, HP 계산 로직 구현
        # 예: LLM에게 공격 대상과 피해량을 한 번 더 추론하게 하거나 룰 북 적용
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        # Todo: 주사위 판정결과를 로직에 녹여넣기
        print(f"주사위 판정결과를 로직에 녹여넣기 → {dice}")

        # mock
        # 범위 공격
        (diffs.append(EntityDiff(entity_id=4, diff={"hp": -8})),)
        (
            relations.append(
                UpdateRelation(
                    cause_entity_id=1,
                    effect_entity_id=4,
                    type=RelationType.HOSTILE,
                )
            ),
        )
        (diffs.append(EntityDiff(entity_id=5, diff={"hp": -11})),)
        (
            relations.append(
                UpdateRelation(
                    cause_entity_id=1,
                    effect_entity_id=7,
                    type=RelationType.HOSTILE,
                )
            ),
        )
        (diffs.append(EntityDiff(entity_id=6, diff={"hp": -9})),)
        (
            relations.append(
                UpdateRelation(
                    cause_entity_id=1,
                    effect_entity_id=7,
                    type=RelationType.HOSTILE,
                )
            ),
        )

        return PhaseUpdate(diffs=diffs, relations=relations)


class DialogueHandler(PhaseHandler):
    async def handle(
        self, request: PlaySceneRequest, analysis: SceneAnalysis, dice: DiceCheckResult
    ) -> PhaseUpdate:
        # 대화 내용에 따른 호감도(Relation) 변화, 아이템 교환 로직
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        # Todo: 주사위 판정결과를 로직에 녹여넣기
        print(f"주사위 판정결과를 로직에 녹여넣기 → {dice}")

        # mock
        diffs.append(
            EntityDiff(entity_id=1, diff={"gold": -50, "item_id": 7, "quantity": 5})
        )

        relations.append(
            UpdateRelation(
                cause_entity_id=1,
                effect_entity_id=7,
                type=RelationType.OWNERSHIP,
            )
        )

        return PhaseUpdate(diffs=diffs, relations=relations)


class ExplorationHandler(PhaseHandler):
    async def handle(
        self, request: PlaySceneRequest, analysis: SceneAnalysis, dice: DiceCheckResult
    ) -> PhaseUpdate:
        # 탐험 활동에 따른 관계 변화 로직 구현
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        # Todo: 주사위 판정결과를 로직에 녹여넣기
        print(f"주사위 판정결과를 로직에 녹여넣기 → {dice}")

        # mock
        relations.append(
            UpdateRelation(
                cause_entity_id=1,
                effect_entity_id=4,
                type=RelationType.LITTLE_FRIENDLY,
            ),
        )

        relations.append(
            UpdateRelation(
                cause_entity_id=1,
                effect_entity_id=5,
                type=RelationType.LITTLE_FRIENDLY,
            ),
        )

        return PhaseUpdate(diffs=diffs, relations=relations)


class RestHandler(PhaseHandler):
    async def handle(
        self, request: PlaySceneRequest, analysis: SceneAnalysis, dice: DiceCheckResult
    ) -> PhaseUpdate:
        # 플레이어의 휴식 활동에 따른 관계 변화 로직 구현
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        # Todo: 주사위 판정결과를 로직에 녹여넣기
        print(f"주사위 판정결과를 로직에 녹여넣기 → {dice}")

        # mock
        diffs.append(EntityDiff(entity_id=1, diff={"hp": 18}))

        return PhaseUpdate(diffs=diffs, relations=relations)


class UnknownHandler(PhaseHandler):
    async def handle(
        self, request: PlaySceneRequest, analysis: SceneAnalysis, dice: DiceCheckResult
    ) -> PhaseUpdate:
        # 플레이어의 알 수 없는 행동에 따른 관계 변화 로직 구현
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        # Todo: 주사위 판정결과를 로직에 녹여넣기
        print(f"주사위 판정결과를 로직에 녹여넣기 → {dice}")

        return PhaseUpdate(diffs=diffs, relations=relations)
