from abc import ABC, abstractmethod
from typing import Any, List

from common.dtos.proxy_service_dto import ProxyService
from domains.gm.gm_service import GmService
from domains.info.enemy_service import EnemyService
from domains.info.item_service import ItemService
from domains.play.dtos.play_dtos import (
    EntityDiff,
    EntityType,
    EntityUnit,
    HandlerUpdatePhase,
    PhaseUpdate,
    PlaySceneRequest,
    RelationType,
    SceneAnalysis,
    UpdateRelation,
)
from domains.play.dtos.player_dtos import (
    FullPlayerState,
    NPCRelation,
    PlayerStateResponse,
)
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
    ) -> PhaseUpdate:
        """각 페이즈에 맞는 로직을 수행하고 변화량(diffs, relations)을 반환합니다."""
        pass

    async def get_player(self, player_id: str) -> FullPlayerState:
        """
        플레이어 상태를 GDB로 관리하는 외부 마이크로서비스를 호출해서 정보를 조회합니다.
        """

        return FullPlayerState(
            player=PlayerStateResponse(hp=150, gold=800, items=[28, 29, 78, 79, 80]),
            player_npc_relations=[
                NPCRelation(
                    npc_id="2", affinity_score=-40, npc_name="그림자 눈 카이엔"
                ),
                NPCRelation(npc_id="5", affinity_score=-30, npc_name="광기 어린 릭스"),
                NPCRelation(npc_id="8", affinity_score=50, npc_name="대장장이 한스"),
                NPCRelation(npc_id="9", affinity_score=50, npc_name="주모 엘리"),
                NPCRelation(npc_id="33", affinity_score=-20, npc_name="공허의 상인"),
                NPCRelation(
                    npc_id="10", affinity_score=50, npc_name="은퇴한 용병 케인"
                ),
                NPCRelation(
                    npc_id="11", affinity_score=50, npc_name="떠돌이 약사 미아"
                ),
            ],
        )

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
    ) -> int:
        """주사위, 아이템, 능력치를 합산하여 플레이어의 최종 전투력을 계산합니다."""
        # 1. 주사위 굴리기 (2d6)
        dice = await gm_service.rolling_dice(2, 6)

        # 2. 아이템 효과 계산
        item_ids = player_state.player.items
        items, _ = await item_service.get_items(item_ids=item_ids, skip=0, limit=100)

        combat_items_effect = sum(
            item["effect_value"] for item in items if item["type"] in ("무기", "방어구")
        )

        # 3. 능력치 (현재 하드코딩)
        ability_score = 2

        total_power = combat_items_effect + ability_score + dice.total

        print(
            f"[전투 판정] 주사위: {dice.total}, 아이템: {combat_items_effect}, 능력치: {ability_score}"
        )
        print(f"-> 최종 플레이어 전투력: {total_power}")

        return total_power

    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
    ) -> HandlerUpdatePhase:
        # 1. 엔티티 분류 및 플레이어 상태 조회
        player_id, player_state, _, enemies, _, _ = await self._categorize_entities(
            request.entities
        )

        if not player_id or not player_state:
            return HandlerUpdatePhase(
                update=PhaseUpdate(diffs=[], relations=request.relations),
                is_success=False,
            )

        # 2. 플레이어 전투력 계산 (중복 로직 통합)
        player_combat_power = await self.calculate_player_combat_power(
            player_state, item_service, gm_service
        )

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

        if player_hp_change != 0:
            diffs.append(
                EntityDiff(state_entity_id=player_id, diff={"hp": player_hp_change})
            )

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=request.relations),
            is_success=is_success,
        )


class NegoHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
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


class DialogueHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
    ) -> HandlerUpdatePhase:
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        social_ability = 3  # 플레이어의 사교 능력치 (임시값)

        (
            player_id,
            player_state,
            npcs,
            enemies,
            items,
            objs,
        ) = await self._categorize_entities(request.entities)

        target_npc_state_id = None
        initial_affinity_score = 0

        # 1. request.relations 목록에서 npc를 찾아 affinity_score 추출하기
        for npc_entity in npcs:
            for rel in request.relations:
                if (
                    rel.cause_entity_id == player_id
                    and rel.effect_entity_id == npc_entity.state_entity_id
                ) or (
                    rel.effect_entity_id == player_id
                    and rel.cause_entity_id == npc_entity.state_entity_id
                ):
                    target_npc_state_id = npc_entity.state_entity_id
                    if rel.affinity_score is not None:
                        initial_affinity_score = rel.affinity_score
                    break
            if target_npc_state_id:
                break

        # 2. affinity_score를 주사위 난이도로 설정하기
        # NPC를 찾을 수 없으면, 기본값 사용
        if not target_npc_state_id:
            affinity_difficulty = -5  # 관계가 없다면 -5로 가정
            print("상호작용중인 NPC가 없습니다. 기본 우호도로 주사위를 굴립니다.")
        else:
            # affinity_score를 주사위 난이도로 설정 (높은 우호도가 낮은 난이도)
            affinity_difficulty = -initial_affinity_score
            print(
                f"NPC {target_npc_state_id}의 초기 우호도: {initial_affinity_score}, 설정 난이도: {affinity_difficulty}"
            )

        dice_result = await gm_service.rolling_dice(social_ability, affinity_difficulty)

        print(
            f"대화 주사위 판정 결과: {dice_result.message} (굴림값: {dice_result.roll_result}, 총합: {dice_result.total}, 성공여부: {dice_result.is_success})"
        )

        # 3. 주사위 차이만큼 우호도 계산해 NPC의 우호도 변경량을 diffs에 반영하기
        if target_npc_state_id:
            affinity_change_amount = 0
            roll_difference = dice_result.total - affinity_difficulty

            if dice_result.is_success:
                affinity_change_amount = max(1, roll_difference)
                print(
                    f"대화 성공! NPC 우호도가 {affinity_change_amount}만큼 증가합니다."
                )
            else:
                affinity_change_amount = min(-1, roll_difference)
                print(
                    f"대화 실패! NPC 우호도가 {abs(affinity_change_amount)}만큼 감소합니다."
                )

            # 우호도 등급 변경 확인
            total_affinity = initial_affinity_score + affinity_change_amount

            relation_grade: RelationType

            if -100 <= total_affinity <= -61:
                relation_grade = RelationType.HOSTILE
            elif -60 <= total_affinity <= -21:
                relation_grade = RelationType.LITTLE_HOSTILE
            elif -20 <= total_affinity <= 20:
                relation_grade = RelationType.NEUTRAL
            elif 21 <= total_affinity <= 60:
                relation_grade = RelationType.LITTLE_FRIENDLY
            elif 61 <= total_affinity <= 100:
                relation_grade = RelationType.FRIENDLY
            else:
                if total_affinity < -100:
                    relation_grade = RelationType.HOSTILE
                elif total_affinity > 100:
                    relation_grade = RelationType.FRIENDLY
                else:
                    relation_grade = RelationType.NEUTRAL

            diffs.append(
                EntityDiff(
                    state_entity_id=target_npc_state_id,
                    diff={"affinity_score": affinity_change_amount},
                )
            )

            relations.append(
                UpdateRelation(
                    cause_entity_id=player_id,
                    effect_entity_id=target_npc_state_id,
                    type=relation_grade,
                    affinity_score=total_affinity,
                )
            )
        else:
            print("대화할 NPC를 찾을 수 없어 우호도 변경을 적용하지 않습니다.")

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=dice_result.is_success,
        )


class ExplorationHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
    ) -> PhaseUpdate:
        (
            player_id,
            player_state,
            npcs,
            enemies,
            items,
            objs,
        ) = await self._categorize_entities(request.entities)
        # 탐험 활동에 따른 관계 변화 로직 구현
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        print("주사위 판정 시작")
        print(f"player → {player_state.player}")

        # mock
        relations.append(
            UpdateRelation(
                cause_entity_id=1,
                effect_entity_id=4,
                type=RelationType.LITTLE_FRIENDLY,
            ),
        )

        relations.append(
            UpdateRelation(
                cause_entity_id=1,
                effect_entity_id=5,
                type=RelationType.LITTLE_FRIENDLY,
            ),
        )

        return PhaseUpdate(diffs=diffs, relations=relations)


class RestHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
    ) -> PhaseUpdate:
        (
            player_id,
            player_state,
            npcs,
            enemies,
            items,
            objs,
        ) = await self._categorize_entities(request.entities)
        # 플레이어의 휴식 활동에 따른 관계 변화 로직 구현
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        # Todo: 주사위 판정결과를 로직에 녹여넣기
        print("주사위 판정결과를 로직에 녹여넣기")
        print(f"player → {player_state.player}")

        # mock
        diffs.append(EntityDiff(entity_id=1, diff={"hp": 18}))

        return PhaseUpdate(diffs=diffs, relations=relations)


class UnknownHandler(PhaseHandler):
    async def handle(
        self,
        request: PlaySceneRequest,
        analysis: SceneAnalysis,
        item_service: ItemService,
        enemy_service: EnemyService,
        gm_service: GmService,
    ) -> HandlerUpdatePhase:
        diffs: List[EntityDiff] = []
        relations: List[UpdateRelation] = []

        return HandlerUpdatePhase(
            update=PhaseUpdate(diffs=diffs, relations=relations),
            is_success=False,
        )
