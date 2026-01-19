from fastapi import APIRouter, Header, HTTPException
from fastapi_utils.cbv import cbv
from jose import jwt

from common.dtos.wrapped_response import WrappedResponse
from configs.setting import ALGORITHM, SECRET_KEY
from src.configs.database import get_db_cursor
from src.domains.auth.dto.login_dtos import LoginRequest, Token  # 정의하신 DTO 임포트

from .auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["인증 및 로그인"])


@cbv(auth_router)
class AuthHandler:
    @auth_router.post(
        "/login",
        summary="로그인",
        response_model=WrappedResponse[Token],  # Dict 대신 Token DTO 사용
    )
    async def login(self, login_data: LoginRequest):  # 스키마 적용
        with get_db_cursor() as cursor:
            # 서비스에 DTO 데이터 전달
            auth_result = AuthService(cursor).authenticate_user(
                login_data.username, login_data.password
            )

            return {
                "data": auth_result,
                "message": f"{login_data.username}님, 환영합니다!",
            }

    @auth_router.post("/logout")
    async def logout(
        self,
        authorization: str = Header(..., description="Bearer <Access_Token>"),
    ):
        try:
            # "Bearer " 문자열 제거 후 토큰만 추출
            token = authorization.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")

            with get_db_cursor() as cursor:
                AuthService(cursor).process_logout(user_id)

            return {"data": None, "message": "성공적으로 로그아웃되었습니다."}
        except Exception:
            raise HTTPException(
                status_code=401, detail="로그아웃 중 오류가 발생했습니다."
            )
