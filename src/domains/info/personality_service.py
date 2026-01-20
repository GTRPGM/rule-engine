from typing import List, Optional

from common.dtos.pagination_meta import PaginationMeta
from utils.load_sql import load_sql


class PersonalityService:
    def __init__(self, cursor):
        self.cursor = cursor
        self.get_personalities_sql = load_sql("info", "get_personalities")
        self.count_personalities_sql = load_sql("info", "count_personalities")

    async def get_personalities(
        self, personality_ids: Optional[List[str]], skip: int, limit: int
    ):
        params = {
            "personality_ids": personality_ids,
            "limit": limit,
            "skip": skip,
        }

        # 전체 개수 조회
        self.cursor.execute(self.count_personalities_sql, params)
        count_result = self.cursor.fetchone()

        total_count = count_result["count"] if count_result else 0

        # 데이터 목록 조회
        self.cursor.execute(self.get_personalities_sql, params)
        personalities = self.cursor.fetchall()

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

        return personalities, meta
