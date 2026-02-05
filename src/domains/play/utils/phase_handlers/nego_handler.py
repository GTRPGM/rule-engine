from configs.llm_manager import LLMManager
from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityDiff,
    HandlerUpdatePhase,
    PhaseUpdate,
    PlaySceneRequest,
    RelationType,
    SceneAnalysis,
    UpdateRelation,
)
from src.domains.play.utils.phase_handlers.phase_handler_base import PhaseHandler
from utils.logger import rule


class NegoHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
        llm: LLMManager,
    ) -> HandlerUpdatePhase:
        (
            player_id,
            player_state,
            npcs,
            enemies,
            items,
            objs,
        ) = await self._categorize_entities(request.entities)
        logs, diffs, relations = [], [], []

        # 1. 아이템 매핑 정보 생성 (ID: State_ID)
        # item_map: {18: "uuid-1234..."} 형태로 저장하여 index() 에러 방지
        item_map = {
            e.entity_id: e.state_entity_id
            for e in items
            if e.entity_id and e.state_entity_id
        }

        # 2. NPC 우호도 조회 (중첩 for문 간소화)
        target_npc_affinity = 0
        npc_state_ids = {n.state_entity_id for n in npcs}
        for rel in request.relations:
            if (
                rel.cause_entity_id == player_id
                and rel.effect_entity_id in npc_state_ids
            ):
                target_npc_affinity = rel.affinity_score or 0
                break

        # 3. 판정 로직
        bargain_ability = 3
        difficulty = -target_npc_affinity
        dice_result = await gm_service.rolling_dice(bargain_ability, difficulty)

        logs.extend(
            [
                f"NPC 우호도: {target_npc_affinity}, 난이도: {difficulty}",
                f"흥정 시도... {dice_result.message} (합계: {dice_result.total})",
            ]
        )
        rule(f"NPC 우호도: {target_npc_affinity}, 난이도: {difficulty}")
        rule(f"흥정 시도... {dice_result.message} (합계: {dice_result.total})")

        # 4. 흥정 성공 처리
        if dice_result.is_success and item_map:
            # DB에서 아이템 상세 정보 가져오기
            item_data, _ = await item_service.get_items(
                item_ids=list(item_map.keys()), skip=0, limit=1
            )

            if item_data:
                target_item = item_data[0]
                item_id = target_item["item_id"]

                # 할인율 계산 및 골드 변동액 산출
                discount_rate = 5 + (dice_result.roll_result - 2) * 2
                final_price = int(target_item["base_price"] * (1 - discount_rate / 100))

                success_log = f"흥정 성공! '{target_item['name']}'을 {discount_rate}% 할인된 {final_price}골드에 구매."
                logs.append(success_log)
                rule(success_log)

                # 거래 수량 확인
                target_entity = next(
                    (e for e in items if e.state_entity_id == item_map[item_id]), None
                )
                current_quantity = (
                    getattr(target_entity, "quantity", 1) if target_entity else 1
                )

                # 소유권 변경 (Relations) - item_map을 사용하여 안전하게 접근
                new_rel = UpdateRelation(
                    cause_entity_id=player_id,
                    effect_entity_id=item_map[item_id],
                    type=RelationType.OWNERSHIP,
                    quantity=current_quantity,
                )
                relations.append(new_rel.model_dump())
                rule(f"relations.append({new_rel.model_dump()})")

                # 골드 차감 (Diffs)
                new_diff = EntityDiff(
                    state_entity_id=player_id, diff={"gold": -final_price}
                )
                diffs.append(new_diff.model_dump())
                rule(f"diffs.append({new_diff.model_dump()})")
            else:
                logs.append("거래 가능한 아이템 정보를 찾을 수 없습니다.")
                rule("거래 가능한 아이템 정보를 찾을 수 없습니다.")

        elif not dice_result.is_success:
            logs.append("흥정 실패! 거래가 성사되지 않았습니다.")
            rule("흥정 실패! 거래가 성사되지 않았습니다.")

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=dice_result.is_success,
            logs=logs,
        )
