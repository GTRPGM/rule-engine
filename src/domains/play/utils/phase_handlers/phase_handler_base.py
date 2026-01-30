from abc import ABC, abstractmethod
from typing import Any, List

from common.dtos.proxy_service_dto import ProxyService
from configs.llm_manager import LLMManager
from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityType,
    PhaseUpdate,
    PlaySceneRequest,
    SceneAnalysis,
)
from domains.play.dtos.player_dtos import FullPlayerState
from src.domains.play.utils.dummy_player import dummy_player
from utils.proxy_request import proxy_request


class PhaseHandler(ABC):
    @abstractmethod
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
        llm: LLMManager,
    ) -> PhaseUpdate:
        """각 페이즈에 맞는 로직을 수행하고 변화량(diffs, relations)을 반환합니다."""
        pass

    async def get_player(self, player_id: str) -> FullPlayerState:
        """
        플레이어 상태를 GDB로 관리하는 외부 마이크로서비스를 호출해서 정보를 조회합니다.
        """

        return dummy_player

        # 준비되는 대로 교체
        return await proxy_request(
            "GET",
            f"/state/player/{player_id}",
            provider=ProxyService.STATE_MANAGER,
        )

    async def _categorize_entities(self, entities: List[Any]):
        player_entity_id = None
        npcs, enemies, drop_items, objects = [], [], [], []

        # 중복 방지를 위해 set을 쓰거나, 필요에 따라 list 유지
        for entity in entities:
            if entity.entity_type == EntityType.PLAYER:
                player_entity_id = entity.state_entity_id
            elif entity.entity_type == EntityType.NPC:
                npcs.append(entity)
            elif entity.entity_type == EntityType.ENEMY:
                enemies.append(entity)
            elif entity.entity_type == EntityType.ITEM:
                drop_items.append(entity)
            elif entity.entity_type == EntityType.OBJECT:
                objects.append(entity)

        player_state = await self.get_player(player_entity_id)

        return player_entity_id, player_state, npcs, enemies, drop_items, objects
