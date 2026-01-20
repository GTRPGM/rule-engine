from typing import List, Optional

from common.dtos.pagination_meta import PaginationMeta
from domains.info.dtos.npc_dtos import NpcDetailResponse
from utils.load_sql import load_sql


class EnemyService:
    def __init__(self, cursor):
        self.cursor = cursor
        self.get_enemies_sql = load_sql("info", "get_enemies")
        self.count_enemies_sql = load_sql("info", "count_enemies")
        self.get_enemy_detail_sql = load_sql("info", "get_enemy_detail")

    async def get_enemies(self, enemy_ids: Optional[List[int]], skip: int, limit: int):
        params = {
            "enemy_ids": enemy_ids if enemy_ids else None,
            "limit": limit,
            "skip": skip,
        }

        # 전체 개수 조회
        self.cursor.execute(self.count_enemies_sql, params)
        count_result = self.cursor.fetchone()

        total_count = count_result["count"] if count_result else 0

        # 데이터 목록 조회
        self.cursor.execute(self.get_enemies_sql, params)
        enemies = self.cursor.fetchall()

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

        return enemies, meta

    async def get_enemy_detail(self, enemy_id: int):
        """
        특정 적의 상세 정보와 전리품(drops) 목록을 통합 조회합니다.
        """
        params = {"enemy_id": enemy_id}

        # 1. 상세 정보 쿼리 실행 (JSON 집계 쿼리 사용 권장)
        # self.get_enemy_detail_sql = load_sql("info", "get_enemy_detail")
        self.cursor.execute(self.get_enemy_detail_sql, params)
        enemy_detail = self.cursor.fetchone()

        # 2. 데이터 존재 여부 확인
        if not enemy_detail or enemy_detail.get("enemy_id") is None:
            return None

        return enemy_detail