from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., examples=["explorer_1"])
    password: str = Field(..., examples=["password123!"])


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    access_token: str = None
    message: str
    user_id: int = None
    detail: str = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str  # 클라이언트가 보낸 리프레시 토큰
