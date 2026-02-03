import logging
from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from psycopg2 import Error as Psycopg2Error

from common.dtos.pagination_meta import PaginationMeta
from domains.session.dtos.session_dtos import (
    SessionRequest,
    SessionResponse,
)
from utils.load_sql import load_sql


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
        except Psycopg2Error as e:
            logging.error(f"Database error in get_user_sessions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="데이터베이스 오류가 발생했습니다.",
            )

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
        except Psycopg2Error as e:
            logging.error(f"Database error in add_user_session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="데이터베이스 오류가 발생했습니다.",
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
        except Psycopg2Error as e:
            logging.error(f"Database error in del_session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="데이터베이스 오류가 발생했습니다.",
            )
        return request.session_id
