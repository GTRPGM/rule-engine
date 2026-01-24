from typing import Any, Optional

from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    # 사용자가 입력한 정답 시도 문구
    user_guess: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="사용자가 입력한 수수께끼 정답 후보",
    )
    current_attempt: Optional[int] = Field(default=None, description="현재 클라이언트상의 시도 횟수")

class AnswerResponse(BaseModel):
    result: str
    message: str
    remaining_time: Any
    fail_count: Optional[int] = None
    explanation: Optional[str] = None


class RiddleData(BaseModel):
    riddle: str = Field(
        description="사용자에게 낼 재미있고 창의적인 수수께끼 질문 내용"
    )
    answer: str = Field(
        description="수수께끼의 정답 (가급적 단어 형태로 명확하게)"
    )
    hint: str = Field(
        description="사용자가 어려워할 때 제공할 짧은 힌트"
    )
    explanation: str = Field(
        description="정답에 대한 간단한 해설"
    )