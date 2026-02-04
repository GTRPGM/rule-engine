from psycopg2 import IntegrityError

from domains.scenario.dtos.scenario_dtos import (
    EnemyCreateRequest,
    EnemyDropCreateRequest,
    ItemCreateRequest,
    NpcCreateRequest,
    NpcInventoryCreateRequest,
)
from utils.load_sql import load_sql
from utils.logger import error


class ScenarioService:
    def __init__(self, cursor):
        self.cursor = cursor
        self.add_item_sql = load_sql("scenario", "add_item")
        self.add_enemy_sql = load_sql("scenario", "add_enemy")
        self.add_npc_sql = load_sql("scenario", "add_npc")
        self.add_enemy_drop_sql = load_sql("scenario", "add_enemy_drop")
        self.add_npc_inventory_sql = load_sql("scenario", "add_npc_inventory")

    async def add_item(self, request: ItemCreateRequest) -> int:
        try:
            item_dict = request.model_dump()
            item_dict["type"] = request.type.value  # Enum을 문자열로 변환

            self.cursor.execute(self.add_item_sql, item_dict)
            result = self.cursor.fetchone()

            if not result:
                raise ValueError("아이템 저장 후 ID를 반환받지 못했습니다.")

            # 3. 성공 시 커밋
            self.cursor.commit()
            return result["item_id"]

        except IntegrityError as e:
            self.cursor.rollback()
            if "already exists" in str(e):
                raise ValueError(f"이미 존재하는 아이템 이름입니다: {request.name}")
            raise ValueError(f"데이터 무결성 오류가 발생했습니다: {str(e)}")

        except Exception as e:
            if self.cursor:
                self.cursor.rollback()
            error(f"[시나리오 서비스 오류] {e}")
            raise e

    async def add_enemy(self, request: EnemyCreateRequest) -> int:
        try:
            item_dict = request.model_dump()

            self.cursor.execute(self.add_enemy_sql, item_dict)
            result = self.cursor.fetchone()

            if not result:
                raise ValueError("아이템 저장 후 ID를 반환받지 못했습니다.")

            # 3. 성공 시 커밋
            self.cursor.commit()
            return result["enemy_id"]

        except IntegrityError as e:
            self.cursor.rollback()
            if "already exists" in str(e):
                raise ValueError(f"이미 존재하는 적 이름입니다: {request.name}")
            raise ValueError(f"데이터 무결성 오류가 발생했습니다: {str(e)}")

        except Exception as e:
            if self.cursor:
                self.cursor.rollback()
            error(f"[시나리오 서비스 오류] {e}")
            raise e

    async def add_enemy_drop(self, request: EnemyDropCreateRequest) -> int:
        try:
            drop_data = request.model_dump()

            self.cursor.execute(self.add_enemy_drop_sql, drop_data)
            result = self.cursor.fetchone()

            if not result:
                raise ValueError("드롭 정보 저장 후 ID를 반환받지 못했습니다.")

            # 3. 성공 시 커밋
            self.cursor.commit()
            return result["drop_id"]

        except IntegrityError as e:
            # 외래키 제약 조건 위반 처리 (enemy_id나 item_id가 없을 때)
            self.cursor.rollback()
            error_msg = str(e)
            if 'is not present in table "enemies"' in error_msg:
                raise ValueError(f"존재하지 않는 적(ID: {request.enemy_id})입니다.")
            elif 'is not present in table "items"' in error_msg:
                raise ValueError(f"존재하지 않는 아이템(ID: {request.item_id})입니다.")
            else:
                raise ValueError(f"데이터 무결성 오류: {error_msg}")

        except Exception as e:
            # 기타 시스템 에러 발생 시 롤백
            if self.cursor:
                self.cursor.rollback()
            error(f"[시나리오 서비스 오류] {e}")
            raise e

    async def add_npc(self, request: NpcCreateRequest) -> int:
        try:
            item_dict = request.model_dump()

            self.cursor.execute(self.add_npc_sql, item_dict)
            result = self.cursor.fetchone()

            if not result:
                raise ValueError("아이템 저장 후 ID를 반환받지 못했습니다.")

            # 3. 성공 시 커밋
            self.cursor.commit()
            return result["npc_id"]

        except IntegrityError as e:
            self.cursor.rollback()
            if "already exists" in str(e):
                raise ValueError(f"이미 존재하는 NPC 이름입니다: {request.name}")
            raise ValueError(f"데이터 무결성 오류가 발생했습니다: {str(e)}")

        except Exception as e:
            if self.cursor:
                self.cursor.rollback()
            error(f"[시나리오 서비스 오류] {e}")
            raise e

    async def add_npc_inventory(self, request: NpcInventoryCreateRequest) -> int:
        try:
            data = request.model_dump()
            self.cursor.execute(self.add_npc_inventory_sql, data)
            result = self.cursor.fetchone()

            if not result:
                raise ValueError("NPC 인벤토리 저장 후 ID를 반환받지 못했습니다.")

            self.cursor.commit()
            return result["inventory_id"]

        except IntegrityError as e:
            self.cursor.rollback()
            error_msg = str(e)
            if "npcs" in error_msg:
                raise ValueError(f"존재하지 않는 NPC(ID: {request.npc_id})입니다.")
            elif "items" in error_msg:
                raise ValueError(f"존재하지 않는 아이템(ID: {request.item_id})입니다.")
            raise ValueError(f"데이터 무결성 오류: {error_msg}")
        except Exception as e:
            if self.cursor:
                self.cursor.rollback()
            raise e
