from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_utils.cbv import cbv

from common.dtos.wrapped_response import WrappedResponse
from common.utils.get_services import get_session_service
from domains.session.dtos.session_dtos import (
    PaginatedSessionResponse,
    SessionRequest,
    SessionResponse,
)
from domains.session.session_service import SessionService

session_router = APIRouter(prefix="/session", tags=["사용자 세션"])

@cbv(session_router)
class SessionRouter:
    @session_router.get(
        "/list",
        summary="사용자 세션 목록 조회",
        response_model=WrappedResponse[PaginatedSessionResponse],
    )
    async def read_user_sessions(
            self,
            user_id: int = Query(..., description="조회할 사용자의 고유 ID", example=1),
            skip: int = Query(0, description="페이지네이션: 건너뛸 항목 수", ge=0),
            limit: int = Query(10, description="페이지네이션: 한 번에 가져올 항목 수", ge=1, le=100),
            is_deleted: bool = Query(False, description="삭제된 세션 포함 여부 (true: 삭제됨, false: 활성 상태)"),
            session_service: SessionService = Depends(get_session_service)
    ):
        try:
            sessions, meta = await session_service.get_user_sessions(user_id, skip, limit, is_deleted)

            return {"data": {"sessions": sessions, "meta": meta}}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"사용자 세션 조회 실패: {str(e)}",
            )

    @session_router.post(
        "/add",
        summary="사용자 세션을 추가합니다.",
        response_model=WrappedResponse[SessionResponse],
    )
    async def add_user_session(
            self,
            request: SessionRequest,
            session_service: SessionService = Depends(get_session_service)
    ):
        try:
            session = await session_service.add_user_session(request)
            return {"data": session}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"사용자 세션 생성 실패: {str(e)}",
            )

    @session_router.delete(
        "/delete",
        summary="사용자 세션을 삭제합니다.",
        response_model=WrappedResponse[str],
    )
    async def delete_user_session(
            self,
            request: SessionRequest,
            session_service: SessionService = Depends(get_session_service)
    ):
        try:
            session_id = await session_service.del_user_session(request)
            return {"data": session_id}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"사용자 세션 생성 실패: {str(e)}",
            )
