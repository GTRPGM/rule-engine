from datetime import datetime
from typing import List

from pydantic import BaseModel

from common.dtos.pagination_meta import PaginationMeta


class SessionResponse(BaseModel):
    user_id: int
    session_id: str
    created_at: datetime

class PaginatedSessionResponse(BaseModel):
    sessions: List[SessionResponse]
    meta: PaginationMeta

class SessionRequest(BaseModel):
    user_id: int
    session_id: str