from typing import List

from configs.llm_manager import LLMManager
from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityDiff,
    EntityUnit,
    HandlerUpdatePhase,
    PhaseUpdate,
    PlaySceneRequest,
    RelationType,
    SceneAnalysis,
    UpdateRelation,
)
from domains.play.dtos.player_dtos import FullPlayerState
from src.domains.play.utils.phase_handlers.phase_handler_base import PhaseHandler


class CombatHandler(PhaseHandler):
    def _get_combat_enemy_details(
        self,
        player_state_id: str,
        relations: List[UpdateRelation],
        entities: List[EntityUnit],
        enemy_details: List[dict],
    ) -> List[dict]:
        """플레이어와 적대 관계인 적들의 상세 정보 목록을 반환합니다."""
        combat_enemies_info = []
        enemy_state_ids = {
            (
                rel.effect_entity_id
                if rel.cause_entity_id == player_state_id
                else rel.cause_entity_id
            )
            for rel in relations
            if rel.type == RelationType.HOSTILE
            and (
                rel.cause_entity_id == player_state_id
                or rel.effect_entity_id == player_state_id
            )
        }

        enemy_id_map = {
            e.state_entity_id: e.entity_id
            for e in entities
            if e.state_entity_id in enemy_state_ids and e.entity_id is not None
        }

        enemy_details_map = {e["enemy_id"]: e for e in enemy_details}

        for state_id in enemy_state_ids:
            rdb_id = enemy_id_map.get(state_id)
            if rdb_id:
                enemy_data = enemy_details_map.get(rdb_id)
                if enemy_data and "base_difficulty" in enemy_data:
                    combat_enemies_info.append(
                        {
                            "rdb_id": rdb_id,
                            "state_id": state_id,
                            "base_difficulty": enemy_data["base_difficulty"],
                        }
                    )
        return combat_enemies_info

    async def calculate_player_combat_power(
        self,
        player_state: FullPlayerState,
        item_service: ItemService,
        gm_service: GmService,
    ) -> tuple[int, List[str]]:
        """주사위, 아이템, 능력치를 합산하여 플레이어의 최종 전투력을 계산합니다."""
        logs: List[str] = []

        # 1. 주사위 굴리기 (2d6)
        dice = await gm_service.rolling_dice(2, 6)

        # 2. 아이템 효과 계산
        item_ids = [int(item.item_id) for item in player_state.player.items]
        items, _ = await item_service.get_items(item_ids=item_ids, skip=0, limit=100)

        combat_items_effect = sum(
            item["effect_value"] for item in items if item["type"] in ("무기", "방어구")
        )

        # 3. 능력치 (현재 하드코딩)
        ability_score = 2

        total_power = combat_items_effect + ability_score + dice.total
        combat_judge_log = f"[전투 판정] 주사위: {dice.total}, 아이템: {combat_items_effect}, 능력치: {ability_score}"
        total_player_power_log = f"-> 최종 플레이어 전투력: {total_power}"
        print(combat_judge_log)
        print(total_player_power_log)
        logs.append(combat_judge_log)
        logs.append(total_player_power_log)

        return total_power, logs

    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
        llm: LLMManager,
    ) -> HandlerUpdatePhase:
        logs: List[str] = []
        # 1. 엔티티 분류 및 플레이어 상태 조회
        player_id, player_state, _, enemies, _, _ = await self._categorize_entities(
            request.entities
        )

        if not player_id or not player_state:
            return HandlerUpdatePhase(
                update=PhaseUpdate(
                    diffs=[], relations=[r.model_dump() for r in request.relations]
                ),
                is_success=False,
            )

        # 2. 플레이어 전투력 계산 (중복 로직 통합)
        player_combat_power, combat_logs = await self.calculate_player_combat_power(
            player_state, item_service, gm_service
        )

        logs.extend(combat_logs)

        # 3. 적 정보 조회
        enemy_ids = list(set([e.entity_id for e in enemies if e.entity_id is not None]))
        enemies_data, _ = await enemy_service.get_enemies(
            enemy_ids=enemy_ids, skip=0, limit=100
        )

        # 4. 현재 교전 중인 적 필터링
        combat_enemy_details = self._get_combat_enemy_details(
            player_state_id=player_id,
            relations=request.relations,
            entities=request.entities,
            enemy_details=enemies_data,
        )

        # 5. 데미지 계산 및 결과 생성
        diffs: List[EntityDiff] = []
        player_hp_change = 0
        is_success = False

        for enemy_info in combat_enemy_details:
            state_entity_id = enemy_info["state_id"]
            enemy_difficulty = enemy_info["base_difficulty"]

            # 난이도와 전투력 차이 계산
            damage_difference = enemy_difficulty - player_combat_power
            is_success = damage_difference < 0

            if damage_difference > 0:
                # 적이 더 강함 -> 플레이어가 데미지 입음
                player_hp_change -= damage_difference
            elif damage_difference < 0:
                # 플레이어가 더 강함 -> 적이 데미지 입음 (음수이므로 양수로 변환)
                diffs.append(
                    EntityDiff(
                        state_entity_id=state_entity_id, diff={"hp": damage_difference}
                    )
                )

            print(f"전투력 차이: {damage_difference}")
            logs.append(f"전투력 차이: {damage_difference}")

        if player_hp_change != 0:
            diffs.append(
                EntityDiff(state_entity_id=player_id, diff={"hp": player_hp_change})
            )

        return HandlerUpdatePhase(
            update=PhaseUpdate(
                diffs=diffs, relations=[r.model_dump() for r in request.relations]
            ),
            is_success=is_success,
            logs=logs,
        )
