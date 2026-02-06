from domains.user.dtos.user_dtos import UserCreateRequest, UserInfo, UserUpdateRequest
from utils.load_sql import load_sql


class UserService:
    def __init__(self, cursor):
        self.cursor = cursor
        self.get_user_sql = load_sql("user", "select_user")
        self.add_user_sql = load_sql("user", "insert_user")
        self.update_user_sql = load_sql("user", "update_user")
        self.del_user_sql = load_sql("user", "delete_user")

    async def create_user(self, request: UserCreateRequest) -> UserInfo:
        self.cursor.execute(self.add_user_sql, request.model_dump())
        user_data = self.cursor.fetchone()

        if user_data:
            return UserInfo(**user_data)

        raise Exception("회원 가입에 실패했습니다.")

    async def update_user(self, request: UserUpdateRequest) -> UserInfo | None:
        self.cursor.execute(self.update_user_sql, request.model_dump())
        user_data = self.cursor.fetchone()

        if user_data:
            return UserInfo(**user_data)
        return None

    async def get_user(self, user_id: int) -> UserInfo | None:
        self.cursor.execute(self.get_user_sql, (user_id,))
        user_data = self.cursor.fetchone()

        if user_data:
            return UserInfo(**user_data)
        return None

    async def del_user(self, user_id: int) -> int | None:
        self.cursor.execute(self.del_user_sql, (user_id,))
        user_data = self.cursor.fetchone()

        if user_data:
            return user_data["user_id"]
        return None
