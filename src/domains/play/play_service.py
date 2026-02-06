from langgraph.graph import END, StateGraph

from configs.llm_manager import LLMManager
from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.info.world_service import WorldService
from domains.play.dtos.play_dtos import (
    PhaseType,
    PhaseUpdate,
    PlaySceneRequest,
    PlaySceneResponse,
    PlaySessionState,
    SceneAnalysis,
)
from domains.play.utils.nodes import (
    analyze_scene_node,
    categorize_entities_node,
    fetch_world_data_node,
)
from domains.play.utils.phase_nodes.combat_node import combat_node
from domains.play.utils.phase_nodes.dialogue_node import dialogue_node
from domains.play.utils.phase_nodes.exploration_node import exploration_node
from domains.play.utils.phase_nodes.nego_node import nego_node
from domains.play.utils.phase_nodes.recovery_node import recovery_node
from domains.play.utils.phase_nodes.rest_node import rest_node
from domains.play.utils.phase_nodes.unknown_node import unknown_node
from utils.logger import rule


class PlayService:
    def __init__(self, cursor, llm_provider="gateway"):
        self.cursor = cursor
        self.llm_manager = LLMManager.get_instance(llm_provider)
        self.analyzer = self.llm_manager.with_structured_output(SceneAnalysis)
        self.gm_service = GmService(cursor)
        self.world_service = WorldService(cursor)
        self.item_service = ItemService(cursor)
        self.enemy_service = EnemyService(cursor)

        # 랭그래프 빌드
        workflow = StateGraph(PlaySessionState)
        rule("랭그래프 빌드")

        # 노드 추가
        workflow.add_node("analyze_scene", analyze_scene_node)
        workflow.add_node("fetch_world_data", fetch_world_data_node)
        workflow.add_node("categorize_entities", categorize_entities_node)
        workflow.add_node("combat", combat_node)
        workflow.add_node("exploration", exploration_node)
        workflow.add_node("dialogue", dialogue_node)
        workflow.add_node("nego", nego_node)
        workflow.add_node("rest", rest_node)
        workflow.add_node("recovery", recovery_node)
        workflow.add_node("unknown", unknown_node)

        # 엔트리 포인트 설정
        workflow.set_entry_point("analyze_scene")

        # 엣지 추가
        workflow.add_edge("analyze_scene", "fetch_world_data")
        workflow.add_edge("fetch_world_data", "categorize_entities")

        # 페이즈 유형에 따라 조건부 간선 추가
        workflow.add_conditional_edges(
            "categorize_entities",
            self._route_phase,
            {
                PhaseType.COMBAT: "combat",
                PhaseType.EXPLORATION: "exploration",
                PhaseType.DIALOGUE: "dialogue",
                PhaseType.NEGO: "nego",
                PhaseType.REST: "rest",
                PhaseType.RECOVERY: "recovery",
                PhaseType.UNKNOWN: "unknown",
            },
        )

        # End points for each phase
        workflow.add_edge("combat", END)
        workflow.add_edge("exploration", END)
        workflow.add_edge("dialogue", END)
        workflow.add_edge("nego", END)
        workflow.add_edge("rest", END)
        workflow.add_edge("recovery", END)
        workflow.add_edge("unknown", END)

        self.graph = workflow.compile()

    def _route_phase(self, state: PlaySessionState):
        """analysis.phase_type 기반으로 적절한 위상 노드로 라우팅합니다."""
        if state.analysis and state.analysis.phase_type:
            return state.analysis.phase_type
        return PhaseType.UNKNOWN

    async def play_scene(self, request: PlaySceneRequest) -> PlaySceneResponse:
        initial_state = PlaySessionState(
            request=request,
            logs=[],
            item_service=self.item_service,
            enemy_service=self.enemy_service,
            gm_service=self.gm_service,
            llm=self.llm_manager,
            world_service=self.world_service,
        )

        final_state: PlaySessionState = await self.graph.ainvoke(initial_state)

        if isinstance(final_state, dict):
            # 딕셔너리 데이터를 기반으로 응답 생성
            analysis = final_state.get("analysis") or initial_state.analysis
            is_success = final_state.get("is_success", False)
            diffs = final_state.get("diffs", [])
            relations = final_state.get("relations", [])
            logs = final_state.get("logs", [])
            phase_type = analysis.phase_type if analysis else PhaseType.UNKNOWN
            reason = analysis.reason if analysis else "분석 실패"
            session_id = request.session_id
            scenario_id = request.scenario_id
        else:
            # 객체인 경우 (기존 로직)
            session_id = final_state.request.session_id
            scenario_id = final_state.request.scenario_id
            phase_type = (
                final_state.analysis.phase_type
                if final_state.analysis
                else PhaseType.UNKNOWN
            )
            reason = (
                final_state.analysis.reason if final_state.analysis else "분석 실패"
            )
            is_success = (
                final_state.is_success if final_state.is_success is not None else False
            )
            diffs = final_state.diffs
            relations = final_state.relations
            logs = final_state.logs

        return PlaySceneResponse(
            session_id=session_id,
            scenario_id=scenario_id,
            phase_type=phase_type,
            reason=reason,
            success=is_success,
            suggested=PhaseUpdate(diffs=diffs, relations=relations),
            value_range=12,
            logs=logs,
        )
