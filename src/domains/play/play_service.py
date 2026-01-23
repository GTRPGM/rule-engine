import os

import aiofiles
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from configs.llm_manager import LLMManager
from configs.setting import APP_ENV
from domains.play.dtos.play_dtos import (
    EntityRelation,
    FeedbackResponse,
    PlaySceneRequest,
    PlaySceneResponse,
    PlaySceneUpdate,
    PlayType,
    SceneAnalysis,
)


class PlayService:
    def __init__(self, cursor, llm_provider="openai"):
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

        updates = []

        if analysis.play_type == PlayType.BATTLE:
            updates.append(
                PlaySceneUpdate(
                    entity_id=1,
                    entity_attribute={"hp": -10},
                    entity_relation=EntityRelation(
                        target_entity_id=2, update_relation="공격"
                    ),
                )
            )
        elif analysis.play_type == PlayType.NEGOTIATE:
            updates.append(
                PlaySceneUpdate(
                    entity_id=1,
                    entity_attribute={"gold": -50},
                    entity_relation=EntityRelation(
                        target_entity_id=3, update_relation="거래"
                    ),
                )
            )
        elif analysis.play_type == PlayType.EXPLORE:
            # 탐험 관련 로직
            print("탐험 관련 로직 실행")
            pass

        return PlaySceneResponse(
            session_id=request.session_id,
            scenario_id=request.scenario_id,
            update=updates,
            feedback=FeedbackResponse(
                play_type=analysis.play_type,
                reason=analysis.reason,
            ),
        )
