from langchain_core.prompts import ChatPromptTemplate

from configs.llm_manager import LLMManager
from domains.play.dtos.play_dtos import (
    EntityRelation,
    PlaySceneRequest,
    PlaySceneResponse,
    PlaySceneUpdate,
    PlayType,
    SceneAnalysis,
)


class PlayService:
    def __init__(self, cursor, llm_provider="gemini"):
        self.cursor = cursor
        self.llm = LLMManager.get_instance(llm_provider)
        self.analyzer = self.llm.with_structured_output(SceneAnalysis)

    async def analyze_scene(self, story: str) -> SceneAnalysis:
        system_instruction = (
            "당신은 게임 시나리오 분석가입니다. 내용을 분석하여 플레이 유형을 결정하세요.\n"
            "1. 전투: 물리적 충돌, 무기 사용, 선공 및 위협 상황\n"
            "2. 협상: 거래, 설득, 정보 교환을 위한 말싸움, 뇌물 수수\n"
            "3. 탐험: 조사, 길 찾기, 함정 해제, 미지의 장소 이동\n"
            "4. 알 수 없음: 캐릭터의 단순 감상, 개인적 잡담, 시스템과 무관한 일상 묘사\n"
            "답변은 반드시 200자 이내의 한국어 문장으로 해야 합니다.\n"
            "만약 상황이 모호하거나 잡설이라면 반드시 '알 수 없음'으로 분류하십시오."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_instruction),
                ("human", "시나리오: {story}"),
            ]
        )

        chain = prompt | self.analyzer
        return await chain.ainvoke({"story": story})

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
            feedback=analysis.play_type,
        )
