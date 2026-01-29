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


class NegoHandler(PhaseHandler):
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
            npcs,
            enemies,
            items,
            objs,
        ) = await self._categorize_entities(request.entities)
        # 대화 내용에 따른 우호도(Relation) 변화, 아이템 교환에 따른 골드 변화 로직
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        # 1. 아이템 정보 사전 생성
        item_ids = list(set([e.entity_id for e in items if e.entity_id is not None]))
        item_data, _ = await item_service.get_items(
            item_ids=item_ids, skip=0, limit=100
        )
        item_dict = {item["item_id"]: item for item in item_data}

        # 2. 흥정 주사위 판정
        bargain_ability = 3  # 플레이어의 흥정 능력치 (임시값)

        # NPC 우호도 점수를 기반으로 흥정 난이도 설정
        target_npc_affinity_score = 0
        for npc_entity in npcs:
            for rel in request.relations:
                if (
                    rel.cause_entity_id == player_id
                    and rel.effect_entity_id == npc_entity.state_entity_id
                ) or (
                    rel.effect_entity_id == player_id
                    and rel.cause_entity_id == npc_entity.state_entity_id
                ):
                    if rel.affinity_score is not None:
                        target_npc_affinity_score = rel.affinity_score
                        break
            if target_npc_affinity_score != 0:
                break

        bargain_difficulty = -target_npc_affinity_score
        print(f"NPC 우호도: {target_npc_affinity_score}")
        print(f"할인 능력치: {bargain_ability}")
        print(f"할인 난이도: {bargain_difficulty}")
        dice_result = await gm_service.rolling_dice(bargain_ability, bargain_difficulty)

        print(
            f"흥정 주사위 판정 결과: {dice_result.message} (굴림값: {dice_result.total}, 성공여부: {dice_result.is_success})"
        )

        # 3. 흥정 결과에 따른 골드 변동치 적용
        bargain_gold_change = 0
        if dice_result.is_success:
            # 거래 대상 아이템 (현재는 scene에 있는 첫 번째 아이템으로 가정)
            if item_dict:
                bargain_item_id = next(iter(item_dict))  # 첫 번째 아이템의 ID를 가져옴
                bargain_item = item_dict[bargain_item_id]
                base_price = bargain_item["base_price"]

                # dice_result.roll_result (2~12)에 따라 할인율 차등 적용 (5% ~ 25%)
                # 2 -> 5%, 12 -> 25%
                discount_percentage = 5 + (dice_result.roll_result - 2) * 2

                discount_amount = base_price * (discount_percentage / 100.0)
                player_payment = base_price - int(discount_amount)  # 소수점 이하 버림

                bargain_gold_change = -player_payment  # 플레이어가 지불하므로 음수
                print(
                    f"흥정 성공! 아이템 '{bargain_item['name']}'을(를) {discount_percentage}% 할인된 가격 {player_payment}골드에 구매합니다."
                )
            else:
                print("흥정 성공! 하지만 거래할 아이템이 없습니다.")
        else:
            # 흥정 실패 시 페널티 (예: 정가 지불 혹은 거래 불가)
            # 여기서는 흥정 실패 시 거래가 성사되지 않는 것으로 가정하고 골드 변화 없음
            print("흥정 실패! 거래가 성사되지 않았습니다.")

        # 플레이어 골드 변동치 적용
        if bargain_gold_change != 0:
            diffs.append(
                EntityDiff(
                    state_entity_id=player_id,
                    diff={"gold": bargain_gold_change},
                )
            )

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=dice_result.is_success,
        )