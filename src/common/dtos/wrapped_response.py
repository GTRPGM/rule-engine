from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

from src.common.dtos.custom import CustomStatus  # 기존 정의된 Enum

T = TypeVar("T")


# Swagger에 표시될 전체 구조 모델
class WrappedResponse(BaseModel, Generic[T]):
    status: CustomStatus = CustomStatus.SUCCESS
    data: T
    message: Optional[str] = None
