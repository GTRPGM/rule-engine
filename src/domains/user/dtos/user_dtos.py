from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserInfo(BaseModel):
    user_id: Optional[int] = None
    username: str
    email: str
    created_at: Optional[datetime] = None


class UserUpdateRequest(BaseModel):
    user_id: int
    username: str
    email: str


class UserCreateRequest(BaseModel):
    username: str
    password_hash: str
    email: str
