from pydantic import BaseModel, Field


class DiceCheckResult(BaseModel):
    message: str = Field(..., description="판정 결과 메시지")
    roll_result: int = Field(..., description="주사위 2개의 합 (2~12)")
    total: int = Field(..., description="주사위 합 + 능력치")
    is_success: bool = Field(..., description="최종 성공 여부")
