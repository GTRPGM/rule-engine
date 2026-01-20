from typing import List, Optional

from common.dtos.pagination_meta import PaginationMeta
from utils.load_sql import load_sql


class NpcService:
    def __init__(self, cursor):
        self.cursor = cursor
        self.get_npcs_sql = load_sql("info", "get_npcs")
        self.count_npcs_sql = load_sql("info", "count_npcs")

    async def get_npcs(self, npc_ids: Optional[List[int]], skip: int, limit: int):
        params = {
            "npc_ids": npc_ids if npc_ids else None,
            "limit": limit,
            "skip": skip,
        }

        # 전체 개수 조회
        self.cursor.execute(self.count_npcs_sql, params)
        count_result = self.cursor.fetchone()
        # RealDictCursor를 사용하므로 키값으로 접근 (count, COUNT(*), 혹은 별칭)
        total_count = count_result["count"] if count_result else 0

        # 데이터 목록 조회
        self.cursor.execute(self.get_npcs_sql, params)
        npcs = self.cursor.fetchall()

        # 페이지네이션 메타데이터 계산
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
        is_last_page = (skip + limit) >= total_count

        meta = PaginationMeta(
            total_count=total_count,
            skip=skip,
            limit=limit,
            is_last_page=is_last_page,
            total_pages=total_pages,
        )

        return npcs, meta
