import os
from typing import List

import aiofiles
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from configs.llm_manager import LLMManager
from configs.setting import APP_ENV
from domains.gm.gm_service import GmService
from domains.play.dtos.play_dtos import (
    EntityDiff,
    PhaseType,
    PhaseUpdate,
    PlaySceneRequest,
    PlaySceneResponse,
    RelationType,
    SceneAnalysis,
    UpdateRelation,
)


class PlayService:
    def __init__(self, cursor, llm_provider="gateway"):
        self.cursor = cursor
        self.llm = LLMManager.get_instance(llm_provider)
        self.analyzer = self.llm.with_structured_output(SceneAnalysis)
        self.gm_service = GmService(cursor)

    async def analyze_scene(self, story: str) -> SceneAnalysis:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "prompts", "instruction.md")

        async with aiofiles.open(prompt_path, mode="r", encoding="utf-8") as f:
            system_instruction = await f.read()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_instruction),
                ("human", "시나리오: {story}"),
            ]
        )

        chain = prompt | self.analyzer
        config: RunnableConfig = {"run_name": f"SceneAnalysis_{APP_ENV}"}

        return await chain.ainvoke({"story": story}, config)

    async def play_scene(self, request: PlaySceneRequest) -> PlaySceneResponse:
        analysis = await self.analyze_scene(request.story)
        print(f"분석된 플레이 유형: {analysis}")

        # Todo: 플레이어 상태 조회 및 주사위 굴리기 → PhaseUpdate
        # player_state = await self.cursor.fetchone()
        dice_chk = await self.gm_service.rolling_dice(3, 12)

        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        # mock
        if analysis.phase_type == PhaseType.COMBAT:
            (
                # 범위 공격
                diffs.append(EntityDiff(entity_id=4, diff={"hp": -8})),
                relations.append(
                    UpdateRelation(
                        cause_entity_id=1,
                        effect_entity_id=4,
                        type=RelationType.HOSTILE,
                    )
                ),
                diffs.append(EntityDiff(entity_id=5, diff={"hp": -11})),
                relations.append(
                    UpdateRelation(
                        cause_entity_id=1,
                        effect_entity_id=7,
                        type=RelationType.HOSTILE,
                    )
                ),
                diffs.append(EntityDiff(entity_id=6, diff={"hp": -9})),
                relations.append(
                    UpdateRelation(
                        cause_entity_id=1,
                        effect_entity_id=7,
                        type=RelationType.HOSTILE,
                    )
                ),
            )
        elif analysis.phase_type == PhaseType.DIALOGUE:
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
        elif analysis.phase_type == PhaseType.EXPLORATION:
            # 탐험 관련 로직 - 일단, 아이템, NPC 발견만 처리 / 나중엔 장소 발견도 추가 예정

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

        return PlaySceneResponse(
            session_id=request.session_id,
            scenario_id=request.scenario_id,
            phase_type=analysis.phase_type,
            reason=analysis.reason,
            success=dice_chk.is_success,
            suggested=PhaseUpdate(diffs=diffs, relations=relations),
            value_range=12,
        )
