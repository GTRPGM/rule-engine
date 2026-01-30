import os
from typing import List

import aiofiles
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from configs.llm_manager import LLMManager
from configs.setting import APP_ENV
from domains.gm.gm_service import GmService
from domains.info.dtos.world_dtos import WorldInfoKey
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.info.world_service import WorldService
from domains.play.dtos.play_dtos import (
    PlaySceneRequest,
    PlaySceneResponse,
    SceneAnalysis,
)
from domains.play.utils.phase_handler_factory import PhaseHandlerFactory


class PlayService:
    def __init__(self, cursor, llm_provider="gateway"):
        self.cursor = cursor
        self.llm = LLMManager.get_instance(llm_provider)
        self.analyzer = self.llm.with_structured_output(SceneAnalysis)
        self.gm_service = GmService(cursor)
        self.world_service = WorldService(cursor)
        self.item_service = ItemService(cursor)
        self.enemy_service = EnemyService(cursor)

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
        logs: List[str] = []
        analysis = await self.analyze_scene(request.story)

        print(f"분석된 플레이 유형: {analysis.phase_type}")
        print(f"분석 근거: {analysis.reason}")
        print(f"분석 확신도: {analysis.confidence}")
        logs.append(f"분석된 플레이 유형: {analysis.phase_type}")
        logs.append(f"사유: {analysis.reason}")
        logs.append(f"분석 확신도: {analysis.confidence}")

        # 분석된 플레이 유형 → 팩토리를 통해 적절한 핸들러 획득
        handler = PhaseHandlerFactory.get_handler(analysis.phase_type)

        # 필요한 경우 RDB에서 필요한 데이터 추가 조회(일단, 장소만)
        world_data = await self.world_service.get_world(
            include_keys=[WorldInfoKey.LOCALES]
        )
        locales = world_data.get("locales", [])
        locale = next(
            (loc for loc in locales if loc["locale_id"] == request.locale_id), None
        )
        print(
            f"장소: {locale['name']} | 식별번호: {locale['locale_id']} | {locale['description']}"
        )

        result = await handler.handle(
            request,
            analysis,
            self.item_service,
            self.enemy_service,
            self.gm_service,
            self.llm,
        )

        if result.logs is not None:
            logs.extend(result.logs)

        return PlaySceneResponse(
            session_id=request.session_id,
            scenario_id=request.scenario_id,
            phase_type=analysis.phase_type,
            reason=analysis.reason,
            success=result.is_success,
            suggested=result.update.model_dump(),
            value_range=12,
            logs=logs,
        )
