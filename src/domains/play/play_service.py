import os

import aiofiles
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from configs.llm_manager import LLMManager
from configs.setting import APP_ENV
from domains.play.dtos.play_dtos import (
    EntityRelation,
    FeedbackResponse,
    PhaseType,
    PhaseUpdate,
    PlaySceneRequest,
    PlaySceneResponse,
    RelationType,
    SceneAnalysis,
)


class PlayService:
    def __init__(self, cursor, llm_provider="gateway"):
        self.cursor = cursor
        self.llm = LLMManager.get_instance(llm_provider)
        self.analyzer = self.llm.with_structured_output(SceneAnalysis)

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
        analysis = await self.analyze_scene(request.data.story)
        print(f"분석된 플레이 유형: {analysis}")

        # Todo: 플레이어 상태 조회 및 주사위 굴리기 → PhaseUpdate
        # player_state = await self.cursor.fetchone()

        updates = []

        # mock
        if analysis.play_type == PhaseType.COMBAT:
            updates.append(
                PhaseUpdate(
                    entity_id=1,
                    entity_attribute={
                        "hp": 3
                    },  # 공격 시 일정 포인트 회복하는 컨셉일 때
                    entity_relation=EntityRelation(
                        target_entity_id=2,
                        update_relation=RelationType.ATTACK,
                        target_entity_attribute={"hp": -10},
                    ),
                )
            )
        elif analysis.play_type == PhaseType.DIALOGUE:
            updates.append(
                PhaseUpdate(
                    entity_id=1,
                    entity_attribute={"gold": -50, "item": 7, "quantity": 5},
                    entity_relation=EntityRelation(
                        target_entity_id=3, update_relation=RelationType.ACQUIRE
                    ),
                )
            )
        elif analysis.play_type == PhaseType.EXPLORATION:
            # 탐험 관련 로직 - 일단, 아이템 발견만 처리 / 나중엔 장소 발견도 추가 예정
            updates.append(
                PhaseUpdate(
                    entity_id=1,
                    entity_attribute={"item": 1, "quantity": 3},
                    entity_relation=EntityRelation(
                        target_entity_id=3, update_relation=RelationType.DISCOVER
                    ),
                )
            )

        return PlaySceneResponse(
            session_id=request.session_id,
            scenario_id=request.scenario_id,
            update=updates,
            feedback=FeedbackResponse(
                play_type=analysis.play_type,
                reason=analysis.reason,
            ),
        )
