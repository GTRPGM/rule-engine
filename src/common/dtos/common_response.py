from fastapi.responses import JSONResponse
from fastapi import status
from typing import Any, Optional, Dict

from src.common.dtos.custom import CustomStatus, CommonResponse


class CustomJSONResponse(JSONResponse):
    """
    모든 성공 응답을 {status: "success", data: ..., message: ...} 포맷으로 자동 래핑하는 커스텀 응답 클래스.
    """

    def __init__(
            self,
            content: Any,
            status_code: int = 200,
            headers: Optional[Dict[str, Any]] = None,
            media_type: Optional[str] = None,
            background: Optional[Any] = None,
            # 커스텀 필드를 추가하여 message와 status를 전달받을 수 있도록 합니다.
            response_message: Optional[str] = None,
            response_status: CustomStatus = CustomStatus.SUCCESS,
    ) -> None:

        # content가 이미 CommonResponse 객체인 경우 (에러 핸들러 등) 처리
        if isinstance(content, dict) and 'status' in content:
            final_content = content
        else:
            # 전달받은 데이터를 CommonResponse 구조의 data 필드에 래핑
            wrapped_content = CommonResponse(
                status=response_status,
                data=content,
                message=response_message,
            )
            final_content = wrapped_content.model_dump(by_alias=True, exclude_none=True)

        super().__init__(
            content=final_content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )