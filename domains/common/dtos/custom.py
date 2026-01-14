from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, Any
from enum import Enum

T = TypeVar('T')


class CustomStatus(str, Enum):
    """응답 상태를 나타내는 Enum"""
    SUCCESS = "success"
    ERROR = "error"
    FAIL = "fail"


class CommonResponse(BaseModel, Generic[T]):
    """
    API 응답의 기본 구조를 정의하는 제네릭 DTO
    """
    status: CustomStatus = Field(CustomStatus.SUCCESS, description="응답 상태 (success, error, fail)")
    data: Optional[T] = Field(None, description="실제 응답 데이터")
    message: Optional[str] = Field(None, description="응답 메시지")

    # HTTP 에러 처리를 위한 필드
    detail: Optional[Any] = Field(None, description="오류 발생 시 상세 정보")

class ErrorResponse(CommonResponse[T]):  # <-- ErrorResponse 정의
    status: CustomStatus = Field(default=CustomStatus.ERROR)
