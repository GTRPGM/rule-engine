from datetime import datetime
from typing import List

from common.dtos.pagination_meta import PaginationMeta
from domains.session.dtos.session_dtos import (
    SessionRequest,
    SessionResponse,
)
from utils.load_sql import load_sql
from utils.logger import warning


def _is_missing_user_sessions_table(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "user_sessions" in message
        and ("does not exist" in message or "undefinedtable" in message)
    )


class SessionService:
    def __init__(self, cursor):
        self.cursor = cursor
        self.get_sessions_sql = load_sql("session", "get_sessions")
        self.count_sessions_sql = load_sql("session", "count_sessions")
        self.insert_session_sql = load_sql("session", "insert_session")
        self.del_session_by_session_id_sql = load_sql(
            "session", "del_session_by_session_id"
        )

    async def get_user_sessions(
        self, user_id: int, skip: int, limit: int, is_deleted: bool = False
    ) -> tuple[List[SessionResponse], PaginationMeta]:
        params = {
            "user_id": user_id,
            "skip": skip,
            "limit": limit,
            "is_deleted": is_deleted,
        }

        try:
            self.cursor.execute(self.count_sessions_sql, params)
            count_result = self.cursor.fetchone()
            total_count = count_result["count"] if count_result else 0

            self.cursor.execute(self.get_sessions_sql, params)
            sessions = self.cursor.fetchall()
        except Exception as exc:
            if not _is_missing_user_sessions_table(exc):
                raise
            warning(
                "user_sessions 테이블이 없어 세션 목록을 빈 값으로 반환합니다: %s",
                exc,
            )
            total_count = 0
            sessions = []

        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
        is_last_page = (skip + limit) >= total_count

        meta = PaginationMeta(
            total_count=total_count,
            skip=skip,
            limit=limit,
            is_last_page=is_last_page,
            total_pages=total_pages,
        )

        return sessions, meta

    async def add_user_session(self, request: SessionRequest) -> SessionResponse:
        params = {
            "user_id": request.user_id,
            "session_id": request.session_id,
        }
        try:
            self.cursor.execute(self.insert_session_sql, params)
            self.cursor.connection.commit()
        except Exception as exc:
            if not _is_missing_user_sessions_table(exc):
                raise
            warning(
                "user_sessions 테이블이 없어 세션 추가를 no-op 처리합니다: %s",
                exc,
            )

        return SessionResponse(
            user_id=request.user_id,
            session_id=request.session_id,
            created_at=datetime.now(),
        )

    async def del_user_session(self, request: SessionRequest) -> str:
        params = {"session_id": request.session_id}
        try:
            self.cursor.execute(self.del_session_by_session_id_sql, params)
            self.cursor.connection.commit()
        except Exception as exc:
            if not _is_missing_user_sessions_table(exc):
                raise
            warning(
                "user_sessions 테이블이 없어 세션 삭제를 no-op 처리합니다: %s",
                exc,
            )
        return request.session_id
