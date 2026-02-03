import asyncio
import json
import random
from datetime import timedelta

from fastapi.encoders import jsonable_encoder
from langchain_core.prompts import ChatPromptTemplate

from configs.llm_manager import LLMManager
from configs.redis_conn import get_redis_client
from domains.info.dtos.world_dtos import WorldInfoKey
from domains.play.dtos.riddle_dtos import AnswerResponse, RiddleData
from domains.play.prompts.answer_validation_prompt import (
    generate_answer_validation_prompt,
)
from domains.play.prompts.prob_generator_prompt import generate_quiz_prompt
from domains.play.prompts.riddle_generator_prompt import generate_riddle_prompt
from utils.load_prompt import load_prompt


class MinigameService:
    def __init__(self, cursor, llm_provider="gateway"):
        self.cursor = cursor
        self.redis = get_redis_client()
        self.REDIS_RIDDLE_PREFIX = "riddle:answer:"
        self.REDIS_WHAT_PREFIX = "quiz:answer:"
        self.examiner = LLMManager.get_instance(
            llm_provider, temperature=0.9
        )  # 문제 생성용 (창의적 - 높은 온도)
        self.evaluator = LLMManager.get_instance(
            llm_provider, temperature=0.0
        )  # 정답 검증용 (정확함 - 낮은 온도)
        self.LIMIT_TIME_MINUTES = 15  # 문제 당 제한 시간
        self.riddle_themes = ["동물", "물건", "자연", "음식", "직업", "추상적인 개념"]
        self.cave_themes = [
            *[info_key.value for info_key in WorldInfoKey],
            "enemies",
            "items",
            "npcs",
            "personalities",
        ]
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    load_prompt(domain="play", filename="riddle_system_prompt.md"),
                ),
                ("human", "{input}"),
            ]
        )
        self.chain = self.prompt | self.examiner

    async def generate_and_save_riddle(self, user_id: int):
        # 1. 구조화된 데이터 생성 (힌트 포함)
        structured_llm = self.examiner.with_structured_output(RiddleData)
        selected_theme = random.choice(self.riddle_themes)
        riddle_obj = await structured_llm.ainvoke(
            generate_riddle_prompt(theme=selected_theme)
        )

        # 2. REDIS에 정보 저장 (fail_count 초기값 0 추가)
        redis_key = f"{self.REDIS_RIDDLE_PREFIX}{user_id}"
        riddle_data_json = json.dumps(
            {
                "answer": riddle_obj.answer,
                "hint": riddle_obj.hint,
                "explanation": riddle_obj.explanation,
                "fail_count": 0,  # 틀린 횟수 추적용
                "total_time_limit": self.LIMIT_TIME_MINUTES * 60,  # 초 단위 저장
            },
            ensure_ascii=False,
        )

        self.redis.setex(redis_key, timedelta(minutes=15), riddle_data_json)

        # 3. 문제 스트리밍
        async def stream_riddle():
            for char in riddle_obj.riddle:
                yield char
                await asyncio.sleep(0.05)

        return stream_riddle()

    async def generate_and_save_quiz(
        self,
        user_id: int,
        item_service,
        enemy_service,
        npc_service,
        personality_service,
        world_service,
    ):
        structured_llm = self.examiner.with_structured_output(RiddleData)
        selected_theme = random.choice(self.cave_themes)
        print(f"selected_theme: {selected_theme}")

        # 1. 테마에 따른 서비스 매핑 (world_service를 기본값으로 설정)
        service_map = {
            "enemies": enemy_service,
            "items": item_service,
            "npcs": npc_service,
            "personalities": personality_service,
        }

        singular_form_map = {
            "enemies": "enemy",
            "items": "item",
            "npcs": "npc",
            "personalities": "personality",
        }

        # 매핑에 없으면 world_service 사용
        info_provider = service_map.get(selected_theme, world_service)

        method_name = (
            f"get_{selected_theme}" if selected_theme in service_map else "get_world"
        )
        method_param = (
            f"{singular_form_map.get(selected_theme, None)}_ids"
            if (selected_theme in service_map.keys())
            else selected_theme
        )

        fetch_method = getattr(info_provider, method_name)

        if selected_theme in service_map.keys():
            params = {method_param: [], "skip": 0, "limit": 500}
            info = await fetch_method(**params)
            if hasattr(info, "data") and info.data is not None:
                info = info.data
        else:
            info = await fetch_method(include_keys=[method_param])

        info = jsonable_encoder(info)

        # 선택된 테마(selected_theme)로 조회된 정보(info)를 토대로 동굴 탐험대 세계관 문제 생성
        quiz_obj = await structured_llm.ainvoke(
            generate_quiz_prompt(theme=selected_theme, info=info)
        )

        redis_key = f"{self.REDIS_WHAT_PREFIX}{user_id}"
        quiz_data_json = json.dumps(
            {
                "answer": quiz_obj.answer,
                "hint": quiz_obj.hint,
                "explanation": quiz_obj.explanation,
                "fail_count": 0,  # 틀린 횟수 추적용
                "total_time_limit": self.LIMIT_TIME_MINUTES * 60,  # 초 단위 저장
            },
            ensure_ascii=False,
        )

        self.redis.setex(redis_key, timedelta(minutes=15), quiz_data_json)

        async def stream_problem():
            for char in quiz_obj.riddle:
                yield char
                await asyncio.sleep(0.05)

        return stream_problem()

    async def check_user_answer(
        self, user_id: int, user_guess: str, flag: str = "RIDDLE"
    ) -> AnswerResponse:
        """사용자의 정답을 검증하는 메인 로직"""
        redis_key = f"{self.REDIS_RIDDLE_PREFIX if flag == 'RIDDLE' else self.REDIS_WHAT_PREFIX}{user_id}"
        stored_data = self.redis.get(redis_key)

        remaining_ttl = self.redis.ttl(redis_key)  # 남은 시간 조회

        if not stored_data or remaining_ttl <= 0:
            return AnswerResponse(
                result="error",
                message="시간이 초과되었거나 진행 중인 퀴즈가 없습니다.",
                remaining_time=0,
            )

        data = json.loads(stored_data)
        correct_answer = data["answer"]

        # LLM을 통한 유연한 정답 체크
        is_correct = await self.validate_with_llm(user_guess, correct_answer)

        if is_correct:
            self.redis.delete(redis_key)
            return AnswerResponse(
                result="correct",
                message="정답입니다! 🎉",
                explanation=data["explanation"],
                remaining_time=remaining_ttl,
            )
        else:
            data["fail_count"] += 1
            fail_count = data["fail_count"]

            # 3번 틀렸을 때 힌트 제공
            if fail_count == 3:
                response_message = f"아쉽게도 틀렸습니다. (힌트: {data['hint']})"
            else:
                response_message = (
                    f"틀렸습니다. 다시 생각해보세요! (현재 {fail_count}회 시도)"
                )

            # 데이터 업데이트 시 TTL 유지
            self.redis.setex(
                redis_key,
                timedelta(seconds=remaining_ttl),
                json.dumps(data, ensure_ascii=False),
            )

            return AnswerResponse(
                result="wrong",
                message=response_message,
                fail_count=fail_count,
                remaining_time=remaining_ttl,
            )

    async def validate_with_llm(self, user_guess: str, correct_answer: str):
        """단순 텍스트 매칭이 아닌 LLM의 판단을 활용"""
        # 1차 비교 (소문자 변환 추가로 더 정확하게)
        if (
            user_guess.strip().replace(" ", "").lower()
            == correct_answer.strip().replace(" ", "").lower()
        ):
            return True

        # 2차 의미적 비교
        check_prompt = generate_answer_validation_prompt(
            correct_answer=correct_answer, user_guess=user_guess
        )
        response = await self.evaluator.ainvoke(check_prompt)

        # "Y"가 포함되어 있는지 검사 (대소문자 무시 및 공백 제거)
        result_text = response.content.strip().upper()
        return "Y" in result_text
