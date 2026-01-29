from typing import List

from configs.llm_manager import LLMManager
from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityDiff,
    HandlerUpdatePhase,
    PhaseUpdate,
    PlaySceneRequest,
    SceneAnalysis,
    UpdateRelation,
)
from src.domains.play.utils.phase_handlers.phase_handler_base import PhaseHandler


class ConsumePotionHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
        llm: LLMManager
    ) -> HandlerUpdatePhase:
        (
            player_id,
            player_state,
            _,
            _,
            _,
            _,
        ) = await self._categorize_entities(request.entities)
        # 플레이어의 휴식 활동에 따른 관계 변화 로직 구현
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        # heal_point = 2  # 기본 턴 당 회복량 - 임의값

        # 플레이어 정보
        print(f"player → {player_state.player}")

        all_player_item_ids = [int(item.item_id) for item in player_state.player.items]
        all_player_items_data, _ = await item_service.get_items(
            item_ids=all_player_item_ids, skip=0, limit=100
        )

        # heal_items = [
        #     item
        #     for item in all_player_items_data
        #     if item["type"] == "소모품" and "포션" in item["name"]
        # ]

        # Todo - heal_items가 하나라도 있다면 해당 아이템을 소모한 결과를 업데이트해 반환해야 합니다.
        #   heal_items가 다수인 경우, 0번째 아이템을 소모합니다.
        #   diff - 회복되는 플레이어 체력 ex: {hp: 10} 을 입력해야 합니다. 회복체력은 item.effect_value입니다.
        #   relations - 소모된 아이템 정보를 입력해야 합니다.

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=True,  # 포션 사용은 절대 실패하지 않습니다.
        )