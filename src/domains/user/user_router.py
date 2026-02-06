from fastapi import APIRouter, HTTPException, status
from fastapi_utils.cbv import Depends, cbv

from common.dtos.wrapped_response import WrappedResponse
from common.utils.get_services import get_user_service
from domains.user.dtos.user_dtos import UserCreateRequest, UserInfo, UserUpdateRequest
from domains.user.user_service import UserService

user_router = APIRouter(prefix="/user", tags=["회원 가입 / 탈퇴"])


@cbv(user_router)
class UserHandler:
    @user_router.get(
        "/{user_id}", response_model=WrappedResponse[UserInfo], summary="회원 정보 조회"
    )
    async def get_user(
        self,
        user_id: int,
        user_service: UserService = Depends(get_user_service),
    ):
        try:
            user = await user_service.get_user(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다.",
                )
            return {"data": user, "message": "회원정보를 조회했습니다."}
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회원정보 조회 중 오류가 발생했습니다: {e}",
            )

    @user_router.post(
        "/create", response_model=WrappedResponse[UserInfo], summary="회원 가입"
    )
    async def create_user(
        self,
        request: UserCreateRequest,
        user_service: UserService = Depends(get_user_service),
    ):
        try:
            user = await user_service.create_user(request)
            return {"data": user, "message": "회원가입이 완료되었습니다."}
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회원 가입 중 오류가 발생했습니다: {e}",
            )

    @user_router.post(
        "/update", response_model=WrappedResponse[UserInfo], summary="회원 정보 수정"
    )
    async def update_user(
        self,
        request: UserUpdateRequest,
        user_service: UserService = Depends(get_user_service),
    ):
        try:
            user = await user_service.update_user(request)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="회원정보가 존재하지 않습니다.",
                )
            return {"data": user, "message": "회원정보가 업데이트되었습니다."}
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회원 정보 수정 중 오류가 발생했습니다: {e}",
            )

    @user_router.delete(
        "/delete/{user_id}", response_model=WrappedResponse[int], summary="회윈 탈퇴"
    )
    async def delete_user(
        self, user_id: int, user_service: UserService = Depends(get_user_service)
    ):
        try:
            user_id = await user_service.del_user(user_id)
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="존재하지 않는 회원입니다.",
                )
            return {"data": user_id, "message": "게임에서 탈퇴했습니다."}
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"회원 탈퇴 중 오류가 발생했습니다: {e}",
            )
