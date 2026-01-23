from langchain_core.prompts import ChatPromptTemplate

from configs.llm_manager import LLMManager


class MinigameService:
    def __init__(self, cursor, llm_provider="gateway"):
        self.cursor = cursor
        self.llm = LLMManager.get_instance(llm_provider)
        # 프롬프트 정의
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "당신은 재미있는 수수께끼를 내는 챗봇입니다."),
                ("human", "{input}"),
            ]
        )

        self.chain = self.prompt | self.llm

    async def validate_with_llm(self, user_guess: str, correct_answer: str):
        check_prompt = f"수수께끼 정답이 '{correct_answer}'일 때, 사용자가 '{user_guess}'라고 답했습니다. 의미상 정답인가요? (Y/N)"
        response = await self.llm.ainvoke(check_prompt)
        return "Y" in response.content

    # async def generate_and_save_riddle(self, user_id: str):
    # Todo: 1. 먼저 구조화된 데이터로 문제와 정답을 가져옴
    #   이 단계는 스트리밍이 아니라 단일 호출(ainvoke)로 처리하여 정답을 확정함
    # structured_llm = self.llm.with_structured_output(RiddleData)
    # riddle_obj = await structured_llm.ainvoke(
    #     "재미있는 수수께끼와 정답을 하나씩 만들어줘."
    # )

    # Todo: 2. DB(또는 cursor)에 정답 저장 (예시 코드)
    # self.cursor.execute("INSERT INTO riddles (user_id, answer) VALUES (?, ?)", (user_id, riddle_obj.answer))

    # 3. 사용자에게는 문제 부분만 스트리밍으로 전달
    # async def stream_riddle():
    #     # 문제 텍스트를 글자 단위로 쪼개서 스트리밍 효과 모사
    #     for char in riddle_obj.riddle:
    #         yield char
    #         await asyncio.sleep(0.05)
    #
    # return stream_riddle()
