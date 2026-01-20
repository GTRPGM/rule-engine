from typing import List, Optional

from domains.info.dtos.world_dtos import WorldInfoKey
from utils.load_sql import load_sql


class WorldService:
    def __init__(self, cursor):
        self.cursor = cursor
        self.get_sys_configs_sql = load_sql("info", "get_sys_configs")
        self.get_world_eras_sql = load_sql("info", "get_world_eras")
        self.get_world_locales_sql = load_sql("info", "get_world_locales")
        self.get_characters_sql = load_sql("info", "get_characters")

    async def get_world(self, include_keys: Optional[List[WorldInfoKey]] = None):
        target_keys = (
            include_keys
            if include_keys
            else ["configs", "eras", "locales", "characters"]
        )

        result = {"configs": None, "eras": None, "locales": None, "characters": None}

        if "configs" in target_keys:
            self.cursor.execute(self.get_sys_configs_sql)
            result["configs"] = self.cursor.fetchall()

        if "eras" in target_keys:
            self.cursor.execute(self.get_world_eras_sql)
            result["eras"] = self.cursor.fetchall()

        if "locales" in target_keys:
            self.cursor.execute(self.get_world_locales_sql)
            result["locales"] = self.cursor.fetchall()

        if "characters" in target_keys:
            self.cursor.execute(self.get_characters_sql)
            result["characters"] = self.cursor.fetchall()

        return result
