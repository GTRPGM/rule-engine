import asyncio
import json
from datetime import timedelta

from langchain_core.prompts import ChatPromptTemplate

from configs.llm_manager import LLMManager
from configs.redis_conn import get_redis_client
from domains.play.dtos.minigame_dtos import RiddleData, AnswerResponse


class MinigameService:
    def __init__(self, cursor, llm_provider="gateway"):
        self.cursor = cursor
        self.redis = get_redis_client()
        self.REDIS_KEY_PREFIX = "riddle:answer:"
        self.llm = LLMManager.get_instance(llm_provider)
        self.LIMIT_TIME_MINUTES = 15  # 문제 당 제한 시간
        # 프롬프트 정의
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "당신은 재미있는 수수께끼를 내는 챗봇입니다."),
                ("human", "{input}"),
            ]
        )
        self.chain = self.prompt | self.llm

    async def generate_and_save_riddle(self, user_id: str):
        # 1. 구조화된 데이터 생성 (힌트 포함)
        structured_llm = self.llm.with_structured_output(RiddleData)
        riddle_obj = await structured_llm.ainvoke(
            "재미있는 수수께끼와 정답, 힌트, 해설을 하나씩 만들어줘."
        )

        # 2. REDIS에 정보 저장 (fail_count 초기값 0 추가)
        redis_key = f"{self.REDIS_KEY_PREFIX}{user_id}"
        riddle_data_json = json.dumps({
            "answer": riddle_obj.answer,
            "hint": riddle_obj.hint,
            "explanation": riddle_obj.explanation,
            "fail_count": 0,  # 틀린 횟수 추적용
            "total_time_limit": self.LIMIT_TIME_MINUTES * 60  # 초 단위 저장
        }, ensure_ascii=False)

        self.redis.setex(redis_key, timedelta(minutes=15), riddle_data_json)

        # 3. 문제 스트리밍
        async def stream_riddle():
            for char in riddle_obj.riddle:
                yield char
                await asyncio.sleep(0.05)

        return stream_riddle()

    async def check_user_answer(self, user_id: int, user_guess: str) -> AnswerResponse:
        """사용자의 정답을 검증하는 메인 로직"""
        redis_key = f"{self.REDIS_KEY_PREFIX}{user_id}"
        stored_data = self.redis.get(redis_key)

        remaining_ttl = self.redis.ttl(redis_key) # 남은 시간 조회

        if not stored_data or remaining_ttl <= 0:
            return AnswerResponse(
                result="error",
                message="시간이 초과되었거나 진행 중인 퀴즈가 없습니다.",
                remaining_time=0
            )

        data = json.loads(stored_data)
        correct_answer = data["answer"]

        # LLM을 통한 유연한 정답 체크
        is_correct = await self.validate_with_llm(user_guess, correct_answer)

        if is_correct:
            self.redis.delete(redis_key)
            return AnswerResponse(
                result="correct",
                message=f"정답입니다! 🎉",
                explanation=data["explanation"],
                remaining_time=remaining_ttl
            )
        else:
            data["fail_count"] += 1
            fail_count = data["fail_count"]

            # 3번 틀렸을 때 힌트 제공
            if fail_count == 3:
                response_message = f"아쉽게도 틀렸습니다. (힌트: {data['hint']})"
            else:
                response_message = f"틀렸습니다. 다시 생각해보세요! (현재 {fail_count}회 시도)"

            # 데이터 업데이트 시 TTL 유지
            self.redis.setex(redis_key, timedelta(seconds=remaining_ttl), json.dumps(data, ensure_ascii=False))

            return AnswerResponse(
                result="wrong",
                message=response_message,
                fail_count=fail_count,
                remaining_time=remaining_ttl
            )

    async def validate_with_llm(self, user_guess: str, correct_answer: str):
        """단순 텍스트 매칭이 아닌 LLM의 판단을 활용"""
        # 1차 비교 (소문자 변환 추가로 더 정확하게)
        if user_guess.strip().replace(" ", "").lower() == correct_answer.strip().replace(" ", "").lower():
            return True

        # 2차 의미적 비교
        check_prompt = f"수수께끼 정답이 '{correct_answer}'일 때, 사용자가 '{user_guess}'라고 답했습니다. 의미상 정답인가요? 오직 Y 또는 N으로만 대답하세요."
        response = await self.llm.ainvoke(check_prompt)

        # "Y"가 포함되어 있는지 검사 (대소문자 무시 및 공백 제거)
        result_text = response.content.strip().upper()
        return "Y" in result_text
