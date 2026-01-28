import os

import aiofiles
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from configs.llm_manager import LLMManager
from configs.setting import APP_ENV
from domains.gm.gm_service import GmService
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

        # 분석된 플레이 유형 → 팩토리를 통해 적절한 핸들러 획득
        handler = PhaseHandlerFactory.get_handler(analysis.phase_type)

        # Todo: 필요하다면 RDB에서 필요한 사전 데이터 조회(플레이어 기본 능력치 등)
        #   → 조회 대상은 영향을 미칠 모든 요소들

        # Todo: 플레이어 상태 조회 및 주사위 굴리기 → PhaseUpdate
        # player_state = await self.cursor.fetchone() # 다른 마이크로 서비스에서 조회 예정
        dice_chk = await self.gm_service.rolling_dice(3, 12)

        # 플레이 유형별 상세 로직 진행 → 룰 엔진에서 제안하는 상태/관계 변경 사항 도출
        suggested_update = await handler.handle(request, analysis, dice_chk)

        return PlaySceneResponse(
            session_id=request.session_id,
            scenario_id=request.scenario_id,
            phase_type=analysis.phase_type,
            reason=analysis.reason,
            success=dice_chk.is_success,
            suggested=suggested_update,
            value_range=12,
        )
