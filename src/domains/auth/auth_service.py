from typing import Any, Dict

from fastapi import HTTPException
from jose import jwt

from src.configs.redis_conn import redis_client
from src.configs.setting import ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS, SECRET_KEY

from .utils.crypt_utils import verify_password
from .utils.token_utils import create_access_token, create_refresh_token


class AuthService:
    def __init__(self, cursor):
        self.cursor = cursor

    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """사용자 인증 및 토큰 세트 발행 (Redis 저장 포함)"""
        # SQL은 파일에서 읽어온다고 가정하거나, 일단 문자열로 정의된 상수를 사용합니다.
        self.cursor.execute(
            "SELECT user_id, username, password_hash FROM users WHERE username = %s AND is_active = TRUE",
            (username,),
        )
        user = self.cursor.fetchone()

        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다."
            )

        token_data = {"sub": str(user["user_id"]), "username": user["username"]}
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        # Redis에 Refresh Token 저장 (Key: user_id)
        redis_client.setex(
            f"refresh_token:{user['user_id']}",
            60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
            refresh_token,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_info": {"user_id": user["user_id"], "username": user["username"]},
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """리프레시 토큰 검증 및 액세스 토큰 재발급"""
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            username: str = payload.get("username")

            # Redis 체크
            saved_token = redis_client.get(f"refresh_token:{user_id}")
            if not saved_token or saved_token != refresh_token:
                raise ValueError("Invalid Refresh Token")

            new_access = create_access_token(
                data={"sub": user_id, "username": username}
            )
            return {"access_token": new_access}

        except Exception:
            raise HTTPException(
                status_code=401, detail="인증이 만료되었습니다. 다시 로그인해주세요."
            )

    def process_logout(self, user_id: str):
        """Redis에서 세션 제거"""
        redis_client.delete(f"refresh_token:{user_id}")
