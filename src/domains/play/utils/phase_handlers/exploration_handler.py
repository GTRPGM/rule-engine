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


class ExplorationHandler(PhaseHandler):
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

        # 탐험 활동에 따른 관계 변화 로직 구현
        logs, diffs, relations = [], [], []

        if not player_id or not player_state:
            no_player_id_log = "⚠️ 경고: 탐색 핸들러에서 플레이어 ID 또는 상태가 누락되었습니다. 플레이어 관련 로직을 건너뛰었습니다."
            logs.append(no_player_id_log)
            rule(no_player_id_log)
            return HandlerUpdatePhase(
                update=PhaseUpdate(diffs=[], relations=[]),
                is_success=True,  # Default to success to continue flow
                logs=["플레이어 정보를 찾을 수 없어 탐험 판정을 건너뜁니다."],
            )

        # 1. 주사위 판정 (플레이어 스탯 연동 권장)
        # player_luck: 플레이어 정보에서 perception(통찰력/인지력) 능력치 찾기(없으면 기본값 2)
        player_luck = getattr(player_state, "perception", 2)
        dice_result = await gm_service.rolling_dice(player_luck, 6)
        logs.append(f"탐험 시도... {dice_result.message} (총합: {dice_result.total})")
        rule(f"탐험 시도... {dice_result.message} (총합: {dice_result.total})")

        # 2. 신규 NPC 필터링 (Set 사용으로 최적화)
        known_npc_ids = {
            rel.npc_id for rel in player_state.player_npc_relations if rel.npc_id
        }
        new_npcs = [n for n in npcs if n.state_entity_id not in known_npc_ids]

        # 3. 아이템 및 오브젝트 습득 (성공 시에만)
        if dice_result.is_success:
            # 아이템/오브젝트 통합 처리
            for loot in items + objs:
                quantity = loot.quantity if loot.quantity is not None else 1
                loot_rel = UpdateRelation(
                    cause_entity_id=player_id,
                    effect_entity_id=loot.state_entity_id,
                    type=RelationType.OWNERSHIP,
                    quantity=quantity,
                )
                relations.append(loot_rel)

            if items or objs:
                total_items_qty = sum(
                    (getattr(item, "quantity", 1) or 1) for item in items
                )
                total_objs_qty = sum((getattr(obj, "quantity", 1) or 1) for obj in objs)
                total_loot_qty = total_items_qty + total_objs_qty

                if len(items) > 0:
                    new_items_log = f"[아이템] {len(items)}종의 아이템 {total_items_qty}개를 획득했습니다."
                    logs.append(new_items_log)
                    rule(new_items_log)

                if len(objs) > 0:
                    new_objs_log = f"[사물] {len(objs)}종의 사물 {total_objs_qty}개를 획득했습니다."
                    logs.append(new_objs_log)
                    rule(new_objs_log)

                new_loots_log = f"[정산] 총 {len(items) + len(objs)}종의 전리품 {total_loot_qty}개를 획득했습니다."
                logs.append(new_loots_log)
                rule(new_loots_log)

        # 4. NPC 관계 처리 (성공/실패 공통 로직 내 분기)
        if new_npcs:
            for npc in new_npcs:
                # 결과에 따른 값 설정
                if dice_result.is_success:
                    affinity = 21 if dice_result.is_critical_success else 0
                    rel_type = (
                        RelationType.LITTLE_FRIENDLY
                        if dice_result.is_critical_success
                        else RelationType.NEUTRAL
                    )
                else:
                    affinity = -60
                    rel_type = RelationType.LITTLE_HOSTILE

                diffs.append(
                    EntityDiff(
                        state_entity_id=player_id,
                        diff={
                            "state_entity_id": npc.state_entity_id,
                            "affinity_score": affinity,
                        },
                    )
                )
                relations.append(
                    UpdateRelation(
                        cause_entity_id=player_id,
                        effect_entity_id=npc.state_entity_id,
                        type=rel_type,
                    )
                )
            new_npc_log = (
                f"{len(new_npcs)}명의 새로운 인연을 만났습니다. (결과: {rel_type})"
            )
            logs.append(new_npc_log)
            rule(new_npc_log)
        elif npcs:
            new_npc_log = "새로운 만남은 없었지만 주변을 탐색했습니다."
            logs.append(new_npc_log)
            rule(new_npc_log)

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=dice_result.is_success,
            logs=logs,
        )
