import os

import aiofiles
from fastapi import HTTPException, status  # Import HTTPException and status
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from common.dtos.proxy_service_dto import ProxyService
from configs.llm_manager import LLMManager
from configs.setting import APP_ENV
from domains.gm.gm_service import GmService
from domains.info.dtos.world_dtos import WorldInfoKey
from domains.info.world_service import WorldService
from domains.play.dtos.play_dtos import (
    EntityType,  # Import EntityType
    PlaySceneRequest,
    PlaySceneResponse,
    SceneAnalysis,
)
from domains.play.dtos.player_dtos import (
    FullPlayerState,
    NPCRelation,
    PlayerStateResponse,
)
from domains.play.utils.phase_handler_factory import PhaseHandlerFactory
from utils.proxy_request import proxy_request


class PlayService:
    def __init__(self, cursor, llm_provider="gateway"):
        self.cursor = cursor
        self.llm = LLMManager.get_instance(llm_provider)
        self.analyzer = self.llm.with_structured_output(SceneAnalysis)
        self.gm_service = GmService(cursor)
        self.world_service = WorldService(cursor)

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

    async def get_player(self, player_id: str) -> FullPlayerState:
        """
        플레이어 상태를 GDB로 관리하는 외부 마이크로서비스를 호출해서 정보를 조회합니다.
        """

        return FullPlayerState(
            player=PlayerStateResponse(hp=150, gold=800, items=[28, 29, 78, 79, 80]),
            player_npc_relations=[
                NPCRelation(npc_id="2", affinity_score=-40, npc_name="그림자 눈 카이엔"),
                NPCRelation(npc_id="5", affinity_score=-30, npc_name="광기 어린 릭스"),
                NPCRelation(npc_id="8", affinity_score=50, npc_name="대장장이 한스"),
                NPCRelation(npc_id="9", affinity_score=50, npc_name="주모 엘리"),
                NPCRelation(npc_id="10", affinity_score=50, npc_name="은퇴한 용병 케인"),
                NPCRelation(npc_id="11", affinity_score=50, npc_name="떠돌이 약사 미아"),
            ]
        )

        # 준비되는 대로 교체
        return await proxy_request(
            "GET",
            f"/state/player/{player_id}",
            provider=ProxyService.STATE_MANAGER,
        )

    async def play_scene(self, request: PlaySceneRequest) -> PlaySceneResponse:
        analysis = await self.analyze_scene(request.story)
        print(f"분석된 플레이 유형: {analysis}")

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
        print(f"locale: {locale}")

        # 플레이어 정보 조회
        player_entity_id = None
        for entity in request.entities:
            if entity.entity_type == EntityType.PLAYER:
                player_entity_id = entity.entity_id
                break

        if not player_entity_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="요청에 플레이어 엔티티가 포함되어 있지 않습니다.",
            )

        player = await self.get_player(player_entity_id)
        print("조회된 플레이어 데이터:", player)


        # Todo: 주사위 굴리기 → PhaseUpdate
        dice_chk = await self.gm_service.rolling_dice(3, 12)

        # Todo: 플레이 유형별 상세 로직 진행 → 룰 엔진에서 제안하는 상태/관계 변경 사항 도출
        suggested_update = await handler.handle(request, analysis, dice_chk, player)

        return PlaySceneResponse(
            session_id=request.session_id,
            scenario_id=request.scenario_id,
            phase_type=analysis.phase_type,
            reason=analysis.reason,
            success=dice_chk.is_success,
            suggested=suggested_update,
            value_range=12,
        )
