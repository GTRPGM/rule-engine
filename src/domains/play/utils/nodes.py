import os
from typing import Any, Dict

import aiofiles
from fastapi import HTTPException, status
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from common.dtos.proxy_service_dto import ProxyService
from configs.setting import APP_ENV
from domains.info.dtos.world_dtos import WorldInfoKey
from domains.info.world_service import WorldService
from domains.play.dtos.play_dtos import (
    EntityType,
    PlaySessionState,
    SceneAnalysis,
)
from domains.play.dtos.player_dtos import FullPlayerState
from utils.logger import error, rule
from utils.proxy_request import proxy_request


async def get_player_state_from_proxy(player_id: str) -> FullPlayerState:
    """
    플레이어 상태를 GDB로 관리하는 외부 마이크로서비스를 호출해서 정보를 조회합니다.
    """
    if not player_id:
        raise HTTPException(status_code=400, detail="유효한 플레이어 ID가 필요합니다.")

    try:
        response = await proxy_request(
            "GET",
            f"/state/player/{player_id}",
            provider=ProxyService.STATE_MANAGER,
        )

        data = response.get("data")

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="플레이어 정보를 찾을 수 없습니다.",
            )

        return FullPlayerState(**data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"플레이어 정보를 찾을 수 없습니다. - {e}",
        )


async def categorize_entities_node(state: PlaySessionState) -> Dict[str, Any]:
    """
    씬의 엔티티를 분류하고 플레이어 상태를 조회하여 상태를 업데이트합니다.
    """
    entities = state.request.entities
    player_entity_id = None
    npcs, enemies, drop_items, objects = [], [], [], []
    logs = state.logs[:]  # Copy logs to avoid modifying in place before returning

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

    player_state = None
    if player_entity_id:
        player_state = await get_player_state_from_proxy(player_entity_id)
    else:
        error("Warning: Scene 내에 플레이어 엔티티가 존재하지 않습니다.")
        logs.append("Warning: Scene 내에 플레이어 엔티티가 존재하지 않습니다.")

    return {
        "player_state": player_state,
        "current_player_id": player_entity_id,
        "npcs": npcs,
        "enemies": enemies,
        "drop_items": drop_items,
        "objects": objects,
        "logs": logs,
    }


async def analyze_scene_node(state: PlaySessionState) -> Dict[str, Any]:
    """
    LLM을 사용하여 스토리를 분석하고 페이즈 유형을 결정합니다.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "..", "prompts", "instruction.md")

    async with aiofiles.open(prompt_path, mode="r", encoding="utf-8") as f:
        system_instruction = await f.read()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_instruction),
            ("human", "시나리오: {story}"),
        ]
    )
    llm_instance = state.llm.with_structured_output(SceneAnalysis)
    chain = prompt | llm_instance
    config: RunnableConfig = {"run_name": f"SceneAnalysis_{APP_ENV}"}

    analysis = await chain.ainvoke({"story": state.request.story}, config)

    logs = state.logs[:]
    logs.append(f"분석된 플레이 유형: {analysis.phase_type}")
    logs.append(f"사유: {analysis.reason}")
    logs.append(f"분석 확신도: {analysis.confidence}")
    rule(f"분석된 플레이 유형: {analysis.phase_type}")
    rule(f"분석 근거: {analysis.reason}")
    rule(f"분석 확신도: {analysis.confidence}")

    return {"analysis": analysis, "logs": logs}


async def fetch_world_data_node(state: PlaySessionState) -> Dict[str, Any]:
    """
    RDB에서 월드 데이터를 조회합니다.
    """
    logs = state.logs[:]
    # world_service가 상태에서 전달되었다고 가정합니다
    world_service: WorldService = state.world_service

    world_data = await world_service.get_world(include_keys=[WorldInfoKey.LOCALES])
    locales = world_data.get("locales", []) or []
    locale = next(
        (loc for loc in locales if loc.get("locale_id") == state.request.locale_id),
        None,
    )
    if locale:
        rule(
            f"장소: {locale.get('name')} | 식별번호: {locale.get('locale_id')} | {locale.get('description')}"
        )
    else:
        rule(f"장소 정보를 찾을 수 없습니다. (ID: {state.request.locale_id})")

    logs.append(f"세계 정보를 불러옵니다.: {world_data}")
    return {"세계 정보": world_data, "logs": logs}


# # --- 페이즈 특화 Nodes ---
#
#
# async def combat_node(state: PlaySessionState) -> Dict[str, Any]:
#     """
#     전투 페이즈 로직을 처리합니다.
#     """
#     logs = state.logs[:]
#     item_service: ItemService = state.item_service
#     enemy_service: EnemyService = state.enemy_service
#     gm_service: GmService = state.gm_service
#     llm: LLMManager = (
#         state.llm
#     )  # CombatHandler에서 직접 사용되지는 않았지만, 필요한 경우 일관성을 유지합니다
#
#     player_id = state.current_player_id
#     player_state = state.player_state
#
#     # 분류된 적 추출
#     entities_in_request = state.request.entities
#     enemies = [e for e in entities_in_request if e.entity_type == EntityType.ENEMY]
#
#     if not player_id or not player_state:
#         logs.append("전투 페이즈: 플레이어 정보를 찾을 수 없습니다.")
#         return {
#             "diffs": state.diffs,
#             "relations": state.relations,
#             "is_success": False,
#             "logs": logs,
#         }
#
#     # _get_combat_emy_details를 복제하고 여기 또는 하위 함수로 _player_combat_power 논리를 계산합니다
#     # 간단하게 하기 위해 관련 부품을 정렬하거나 새로운 도우미 함수를 호출하겠습니다
#
#     # 적 상세정보 조회
#     combat_enemies_info = []
#     enemy_state_ids = {
#         (
#             rel.effect_entity_id
#             if rel.cause_entity_id == player_id
#             else rel.cause_entity_id
#         )
#         for rel in state.request.relations
#         if rel.type == RelationType.HOSTILE
#         and (rel.cause_entity_id == player_id or rel.effect_entity_id == player_id)
#     }
#
#     enemy_id_map = {
#         e.state_entity_id: e.entity_id
#         for e in entities_in_request
#         if e.state_entity_id in enemy_state_ids and e.entity_id is not None
#     }
#
#     enemy_rdb_ids = list(set([e.entity_id for e in enemies if e.entity_id is not None]))
#     enemies_data, _ = await enemy_service.get_enemies(
#         enemy_ids=enemy_rdb_ids, skip=0, limit=100
#     )
#     enemy_details_map = {e["enemy_id"]: e for e in enemies_data}
#
#     for state_id in enemy_state_ids:
#         rdb_id = enemy_id_map.get(state_id)
#         if rdb_id:
#             enemy_data = enemy_details_map.get(rdb_id)
#             if enemy_data and "base_difficulty" in enemy_data:
#                 combat_enemies_info.append(
#                     {
#                         "rdb_id": rdb_id,
#                         "state_id": state_id,
#                         "base_difficulty": enemy_data["base_difficulty"],
#                     }
#                 )
#
#     # Logic from CombatHandler.calculate_player_combat_power
#     combat_logs: List[str] = []
#     dice = await gm_service.rolling_dice(2, 6)
#     dice_result_log = f"전투 시도... {dice.message}{' | 잭팟!!' if dice.is_critical_success else ''} | 굴림값 {dice.roll_result} + 능력보정치 {dice.ability_score} = 총합 {dice.total}"
#     rule(dice_result_log)
#     combat_logs.append(dice_result_log)
#
#     combat_items_effect = 0
#     item_ids = [int(item.item_id) for item in player_state.player.items]
#     if len(item_ids) > 0:
#         items, _ = await item_service.get_items(item_ids=item_ids, skip=0, limit=100)
#         combat_items_effect = sum(
#             item["effect_value"] for item in items if item["type"] in ("무기", "방어구")
#         )
#
#     ability_score = 2  # Hardcoded
#     player_combat_power = combat_items_effect + ability_score + dice.total
#     combat_judge_log = f"[전투 판정] 주사위: {dice.total}, 아이템: {combat_items_effect}, 능력치: {ability_score}"
#     total_player_power_log = f"최종 플레이어 전투력: {player_combat_power}"
#     rule(combat_judge_log)
#     rule(total_player_power_log)
#     combat_logs.append(combat_judge_log)
#     combat_logs.append(total_player_power_log)
#     logs.extend(combat_logs)
#
#     # 피해 계산 및 결과 생성
#     diffs: List[EntityDiff] = []
#     is_success = False
#
#     for enemy_info in combat_enemies_info:
#         enemy_state_id = enemy_info["state_id"]
#         enemy_difficulty = enemy_info["base_difficulty"]
#         logs.append(f"적 식별번호: {enemy_state_id} | 적 전투력: {enemy_difficulty}")
#         rule(f"적 식별번호: {enemy_state_id} | 적 전투력: {enemy_difficulty}")
#
#         power_gap = player_combat_power - enemy_difficulty
#         result_text = (
#             "승리" if power_gap > 0 else ("무승부" if power_gap == 0 else "패배")
#         )
#         logs.append(f"전투 결과: {result_text} | 전투력 차이: {power_gap}")
#         rule(f"전투 결과: {result_text} | 전투력 차이: {power_gap}")
#
#         if power_gap > 0:
#             is_success = True
#             new_diff = EntityDiff(
#                 state_entity_id=enemy_state_id,
#                 diff={"hp": -power_gap},
#             )
#             diffs.append(new_diff)
#             logs.append(f"전투 승리! 적에게 {power_gap}의 데미지를 입혔습니다.")
#
#         elif power_gap < 0:
#             is_success = False
#             new_diff = EntityDiff(
#                 state_entity_id=player_id,
#                 diff={"hp": power_gap},
#             )
#             diffs.append(new_diff)
#             logs.append(f"전투 패배... 플레이어가 {-power_gap}의 데미지를 입었습니다.")
#         else:
#             logs.append("막상막하의 대결이었습니다!")
#
#     return {
#         "diffs": diffs,
#         "relations": state.relations,  # 관계는 전투 핸들러에서 직접 업데이트되지 않고 통과
#         "is_success": is_success,
#         "logs": logs,
#     }
#
#
# async def exploration_node(state: PlaySessionState) -> Dict[str, Any]:
#     logs = state.logs[:]
#     diffs = state.diffs[:]
#     relations = state.relations[:]
#
#     player_id = state.current_player_id
#     player_state = state.player_state
#     npcs = state.npcs
#     items = state.drop_items
#     objs = state.objects
#
#     gm_service: GmService = state.gm_service
#
#     if not player_id or not player_state:
#         no_player_id_log = "⚠️ 경고: 탐색 핸들러에서 플레이어 ID 또는 상태가 누락되었습니다. 플레이어 관련 로직을 건너뛰었습니다."
#         logs.append(no_player_id_log)
#         rule(no_player_id_log)
#         return {
#             "diffs": diffs,
#             "relations": relations,
#             "is_success": True,
#             "logs": logs + ["플레이어 정보를 찾을 수 없어 탐험 판정을 건너뜁니다."],
#         }
#
#     # 1. 주사위 판정 (플레이어 스탯 연동 권장)
#     player_luck = getattr(player_state, "perception", 2)
#     dice_result = await gm_service.rolling_dice(player_luck, 6)
#     logs.append(f"탐험 시도... {dice_result.message} (총합: {dice_result.total})")
#     rule(f"탐험 시도... {dice_result.message} (총합: {dice_result.total})")
#
#     # 2. 신규 NPC 필터링 (Set 사용으로 최적화)
#     known_npc_ids = {
#         rel.npc_id for rel in player_state.player.npc_relations if rel.npc_id
#     }
#     new_npcs = [n for n in npcs if n.state_entity_id not in known_npc_ids]
#
#     # 3. 아이템 및 오브젝트 습득 (성공 시에만)
#     if dice_result.is_success:
#         for loot in items + objs:
#             quantity = loot.quantity if loot.quantity is not None else 1
#             loot_rel = UpdateRelation(
#                 cause_entity_id=player_id,
#                 effect_entity_id=loot.state_entity_id,
#                 type=RelationType.OWNERSHIP,
#                 quantity=quantity,
#             )
#             relations.append(loot_rel)
#
#         if items or objs:
#             total_items_qty = sum((getattr(item, "quantity", 1) or 1) for item in items)
#             total_objs_qty = sum((getattr(obj, "quantity", 1) or 1) for obj in objs)
#             total_loot_qty = total_items_qty + total_objs_qty
#
#             if len(items) > 0:
#                 new_items_log = f"[아이템] {len(items)}종의 아이템 {total_items_qty}개를 획득했습니다."
#                 logs.append(new_items_log)
#                 rule(new_items_log)
#
#             if len(objs) > 0:
#                 new_objs_log = (
#                     f"[사물] {len(objs)}종의 사물 {total_objs_qty}개를 획득했습니다."
#                 )
#                 logs.append(new_objs_log)
#                 rule(new_objs_log)
#
#             new_loots_log = f"[정산] 총 {len(items) + len(objs)}종의 전리품 {total_loot_qty}개를 획득했습니다."
#             logs.append(new_loots_log)
#             rule(new_loots_log)
#
#     # 4. NPC 관계 처리 (성공/실패 공통 로직 내 분기)
#     if new_npcs:
#         for npc in new_npcs:
#             if dice_result.is_success:
#                 affinity = 21 if dice_result.is_critical_success else 0
#                 rel_type = (
#                     RelationType.LITTLE_FRIENDLY
#                     if dice_result.is_critical_success
#                     else RelationType.NEUTRAL
#                 )
#             else:
#                 affinity = -60
#                 rel_type = RelationType.LITTLE_HOSTILE
#
#             relations.append(
#                 UpdateRelation(
#                     cause_entity_id=player_id,
#                     effect_entity_id=npc.state_entity_id,
#                     type=rel_type,
#                     affinity_score=affinity,
#                 )
#             )
#         new_npc_log = (
#             f"{len(new_npcs)}명의 새로운 인연을 만났습니다. (결과: {rel_type})"
#         )
#         logs.append(new_npc_log)
#         rule(new_npc_log)
#     elif npcs:
#         new_npc_log = "새로운 만남은 없었지만 주변을 탐색했습니다."
#         logs.append(new_npc_log)
#         rule(new_npc_log)
#
#     return {
#         "diffs": diffs,
#         "relations": relations,
#         "is_success": dice_result.is_success,
#         "logs": logs,
#     }
#
#
# async def dialogue_node(state: PlaySessionState) -> Dict[str, Any]:
#     logs = state.logs[:]
#     diffs = state.diffs[:]
#     relations = state.relations[:]
#
#     player_id = state.current_player_id
#     player_state = state.player_state
#     npcs = state.npcs
#
#     gm_service: GmService = state.gm_service
#
#     if not player_id or not player_state:
#         logs.append("대화 페이즈: 플레이어 정보를 찾을 수 없습니다.")
#         return {
#             "diffs": diffs,
#             "relations": relations,
#             "is_success": False,
#             "logs": logs,
#         }
#
#     social_ability = 3
#
#     target_npc_state_id = None
#     initial_affinity_score = 0
#
#     for npc_entity in npcs:
#         for rel in state.request.relations:
#             if (
#                 rel.cause_entity_id == player_id
#                 and rel.effect_entity_id == npc_entity.state_entity_id
#             ) or (
#                 rel.effect_entity_id == player_id
#                 and rel.cause_entity_id == npc_entity.state_entity_id
#             ):
#                 target_npc_state_id = npc_entity.state_entity_id
#                 if rel.affinity_score is not None:
#                     initial_affinity_score = rel.affinity_score
#                 break
#         if target_npc_state_id:
#             break
#
#     if not target_npc_state_id:
#         affinity_difficulty = -5
#         rule("상호작용중인 NPC가 없습니다. 기본 우호도로 주사위를 굴립니다.")
#         logs.append("상호작용중인 NPC가 없습니다. 기본 우호도로 주사위를 굴립니다.")
#     else:
#         affinity_difficulty = -initial_affinity_score
#         affinity_score_log = f"NPC {target_npc_state_id}의 초기 우호도: {initial_affinity_score}, 설정 난이도: {affinity_difficulty}"
#         rule(affinity_score_log)
#         logs.append(affinity_score_log)
#
#     dice_result = await gm_service.rolling_dice(social_ability, affinity_difficulty)
#     dice_result_log = f"대화 시도... {dice_result.message}{' | 잭팟!!' if dice_result.is_critical_success else ''} | 굴림값 {dice_result.roll_result} + 능력보정치 {dice_result.ability_score} = 총합 {dice_result.total}"
#
#     rule(dice_result_log)
#     logs.append(dice_result_log)
#
#     if target_npc_state_id:
#         affinity_change_amount = 0
#         roll_difference = dice_result.total - affinity_difficulty
#
#         if dice_result.is_success:
#             affinity_change_amount = max(1, roll_difference)
#             success_log = (
#                 f"대화 성공! NPC 우호도가 {affinity_change_amount}만큼 증가합니다."
#             )
#             rule(success_log)
#             logs.append(success_log)
#         else:
#             affinity_change_amount = min(-1, roll_difference)
#             fail_log = (
#                 f"대화 실패! NPC 우호도가 {abs(affinity_change_amount)}만큼 감소합니다."
#             )
#             rule(fail_log)
#             logs.append(fail_log)
#
#         total_affinity = initial_affinity_score + affinity_change_amount
#
#         relation_grade: RelationType
#
#         if -100 <= total_affinity <= -61:
#             relation_grade = RelationType.HOSTILE
#         elif -60 <= total_affinity <= -21:
#             relation_grade = RelationType.LITTLE_HOSTILE
#         elif -20 <= total_affinity <= 20:
#             relation_grade = RelationType.NEUTRAL
#         elif 21 <= total_affinity <= 60:
#             relation_grade = RelationType.LITTLE_FRIENDLY
#         elif 61 <= total_affinity <= 100:
#             relation_grade = RelationType.FRIENDLY
#         else:
#             if total_affinity < -100:
#                 relation_grade = RelationType.HOSTILE
#             elif total_affinity > 100:
#                 relation_grade = RelationType.FRIENDLY
#             else:
#                 relation_grade = RelationType.NEUTRAL
#
#         new_rel = UpdateRelation(
#             cause_entity_id=player_id,
#             effect_entity_id=target_npc_state_id,
#             type=relation_grade,
#             affinity_score=affinity_change_amount,
#         )
#
#         relations.append(new_rel)
#         rule(f"relations.append({new_rel.model_dump()})")
#         logs.append(f"relations.append({new_rel.model_dump()})")
#     else:
#         rule("대화할 NPC를 찾을 수 없어 우호도 변경을 적용하지 않습니다.")
#         logs.append("대화할 NPC를 찾을 수 없어 우호도 변경을 적용하지 않습니다.")
#
#     return {
#         "diffs": diffs,
#         "relations": relations,
#         "is_success": dice_result.is_success,
#         "logs": logs,
#     }
#
#
# async def nego_node(state: PlaySessionState) -> Dict[str, Any]:
#     logs = state.logs[:]
#     diffs = state.diffs[:]
#     relations = state.relations[:]
#
#     player_id = state.current_player_id
#     player_state = state.player_state
#     npcs = state.npcs
#     items = state.drop_items
#
#     gm_service: GmService = state.gm_service
#     item_service: ItemService = state.item_service
#
#     if not player_id or not player_state:
#         logs.append("흥정 페이즈: 플레이어 정보를 찾을 수 없습니다.")
#         return {
#             "diffs": diffs,
#             "relations": relations,
#             "is_success": False,
#             "logs": logs,
#         }
#
#     # 1. 아이템 매핑 정보 생성 (ID: State_ID)
#     item_map = {
#         e.entity_id: e.state_entity_id
#         for e in items
#         if e.entity_id and e.state_entity_id
#     }
#
#     # 2. NPC 우호도 조회 (중첩 for문 간소화)
#     target_npc_affinity = 0
#     npc_state_ids = {n.state_entity_id for n in npcs}
#     for rel in state.request.relations:
#         if rel.cause_entity_id == player_id and rel.effect_entity_id in npc_state_ids:
#             target_npc_affinity = rel.affinity_score or 0
#             break
#
#     # 3. 판정 로직
#     bargain_ability = 3
#     difficulty = -target_npc_affinity
#     dice_result = await gm_service.rolling_dice(bargain_ability, difficulty)
#
#     logs.extend(
#         [
#             f"NPC 우호도: {target_npc_affinity}, 난이도: {difficulty}",
#             f"흥정 시도... {dice_result.message} (합계: {dice_result.total})",
#         ]
#     )
#     rule(f"NPC 우호도: {target_npc_affinity}, 난이도: {difficulty}")
#     rule(f"흥정 시도... {dice_result.message} (합계: {dice_result.total})")
#
#     # 4. 흥정 성공 처리
#     if dice_result.is_success and item_map:
#         item_data, _ = await item_service.get_items(
#             item_ids=list(item_map.keys()), skip=0, limit=1
#         )
#
#         if item_data:
#             target_item = item_data[0]
#             item_id = target_item["item_id"]
#
#             discount_rate = 5 + (dice_result.roll_result - 2) * 2
#             final_price = int(target_item["base_price"] * (1 - discount_rate / 100))
#
#             success_log = f"흥정 성공! '{target_item['name']}'을 {discount_rate}% 할인된 {final_price}골드에 구매."
#             logs.append(success_log)
#             rule(success_log)
#
#             target_entity = next(
#                 (e for e in items if e.state_entity_id == item_map[item_id]), None
#             )
#             current_quantity = (
#                 getattr(target_entity, "quantity", 1) if target_entity else 1
#             )
#
#             new_rel = UpdateRelation(
#                 cause_entity_id=player_id,
#                 effect_entity_id=item_map[item_id],
#                 type=RelationType.OWNERSHIP,
#                 quantity=current_quantity,
#             )
#             relations.append(new_rel)
#             rule(f"relations.append({new_rel.model_dump()})")
#
#             new_diff = EntityDiff(
#                 state_entity_id=player_id, diff={"gold": -final_price}
#             )
#             diffs.append(new_diff)
#             rule(f"diffs.append({new_diff.model_dump()})")
#         else:
#             logs.append("거래 가능한 아이템 정보를 찾을 수 없습니다.")
#             rule("거래 가능한 아이템 정보를 찾을 수 없습니다.")
#
#     elif not dice_result.is_success:
#         logs.append("흥정 실패! 거래가 성사되지 않았습니다.")
#         rule("흥정 실패! 거래가 성사되지 않았습니다.")
#
#     return {
#         "diffs": diffs,
#         "relations": relations,
#         "is_success": dice_result.is_success,
#         "logs": logs,
#     }
#
#
# async def rest_node(state: PlaySessionState) -> Dict[str, Any]:
#     logs = state.logs[:]
#     diffs = state.diffs[:]
#     relations = state.relations[:]
#
#     player_id = state.current_player_id
#     player_state = state.player_state
#
#     gm_service: GmService = state.gm_service
#
#     if not player_id or not player_state:
#         logs.append("휴식 페이즈: 플레이어 정보를 찾을 수 없습니다.")
#         return {
#             "diffs": diffs,
#             "relations": relations,
#             "is_success": False,
#             "logs": logs,
#         }
#
#     heal_point = 2
#
#     dice_result = await gm_service.rolling_dice(heal_point, 6)
#     dice_result_log = f"휴식 시도... {dice_result.message}{' | 잭팟!!' if dice_result.is_critical_success else ''} | 굴림값 {dice_result.roll_result} + 능력보정치 {dice_result.ability_score} = 총합 {dice_result.total}"
#     rule(dice_result_log)
#     logs.append(dice_result_log)
#
#     additional_healing: int = 0
#     if dice_result.is_critical_success:
#         additional_healing = dice_result.total
#     elif dice_result.is_success:
#         additional_healing = dice_result.total // 2
#     else:
#         additional_healing = 0
#
#     total_healing = heal_point + additional_healing
#     if dice_result.is_success:
#         success_log = f"""회복 성공: {dice_result.is_success} | 총 회복량(주사위 합 {dice_result.total} {"" if dice_result.is_critical_success else "/ 2"} + 기본 회복량 {heal_point}): {total_healing}"""
#         rule(success_log)
#         logs.append(success_log)
#     else:
#         fail_log = f"""회복 성공: {dice_result.is_success} | 총 회복량 = 기본 회복량 {heal_point}): {total_healing}"""
#         rule(fail_log)
#         logs.append(fail_log)
#
#     new_diff = EntityDiff(state_entity_id=player_id, diff={"hp": total_healing})
#     diffs.append(new_diff)
#     rule(f"diffs.append({new_diff.model_dump()})")
#
#     return {
#         "diffs": diffs,
#         "relations": relations,
#         "is_success": dice_result.is_success,
#         "logs": logs,
#     }
#
#
# from src.domains.play.prompts.potion_selection_prompt import (
#     create_potion_selection_prompt,
# )
#
#
# async def recovery_node(state: PlaySessionState) -> Dict[str, Any]:
#     logs = state.logs[:]
#     diffs = state.diffs[:]
#     relations = state.relations[:]
#
#     player_id = state.current_player_id
#     player_state = state.player_state
#
#     item_service: ItemService = state.item_service
#     gm_service: GmService = state.gm_service
#     llm: LLMManager = state.llm
#
#     is_success = False
#
#     if not player_id or not player_state:
#         logs.append("회복 페이즈: 플레이어 정보를 찾을 수 없습니다.")
#         return {
#             "diffs": diffs,
#             "relations": relations,
#             "is_success": is_success,
#             "logs": logs,
#         }
#
#     # 1. 플레이어 인벤토리에서 포션 찾기
#     item_ids = [int(item.item_id) for item in player_state.player.items]
#     heal_items = None
#     if len(item_ids) > 0:
#         items, _ = await item_service.get_items(item_ids=item_ids, skip=0, limit=100)
#
#         heal_items = [
#             item
#             for item in items
#             if "소모품" == item["type"] and "포션" in item["name"]
#         ]
#
#     consumed_potion = None
#     effect_value: int = 0
#
#     if heal_items:
#         is_success = True
#         if len(heal_items) > 1:
#             potion_names = [item["name"] for item in heal_items]
#             prompt = create_potion_selection_prompt(potion_names, state.request.story)
#
#             try:
#                 llm_response = await llm.ainvoke(prompt)
#                 potion_name_from_llm = llm_response.content.strip()
#                 found_potion = next(
#                     (
#                         item
#                         for item in heal_items
#                         if item["name"] == potion_name_from_llm
#                     ),
#                     None,
#                 )
#                 if found_potion:
#                     consumed_potion = found_potion
#                 else:
#                     consumed_potion = heal_items[0]
#
#                 rule(
#                     f"[소모 아이템 정보] {consumed_potion['name']} | 치유량: {consumed_potion['effect_value']}"
#                 )
#                 logs.append(
#                     f"[소모 아이템 정보] {consumed_potion['name']} | 치유량: {consumed_potion['effect_value']}"
#                 )
#             except Exception:
#                 consumed_potion = heal_items[0]
#         else:
#             consumed_potion = heal_items[0]
#
#         if consumed_potion:
#             effect_value = consumed_potion["effect_value"]
#
#     else:
#         logs.append("이런! 보유한 포션이 하나도 없습니다.")
#         rule("이런! 보유한 포션이 하나도 없습니다.")
#
#     # 2. 추가 치유량 계산
#     additional_heal_point: int = 0
#     heal_point = 2
#     if effect_value > 0:
#         dice_result = await gm_service.rolling_dice(heal_point, effect_value)
#         dice_result_log = f"추가 치유 시도... {dice_result.message}{' | 잭팟!!' if dice_result.is_critical_success else ''} | 굴림값 {dice_result.roll_result} + 능력보정치 {dice_result.ability_score} = 총합 {dice_result.total}"
#         logs.append(dice_result_log)
#         rule(dice_result_log)
#
#         if dice_result.is_critical_success:
#             additional_heal_point = heal_point * 2
#             additional_heal_log = (
#                 f"두 배 추가 치유 포인트가 적용됩니다. +{additional_heal_point} "
#             )
#             rule(additional_heal_log)
#             logs.append(additional_heal_log)
#         elif dice_result.is_success:
#             additional_heal_point = heal_point
#             additional_heal_log = (
#                 f"추가 치유 포인트가 적용됩니다. +{additional_heal_point}"
#             )
#             rule(additional_heal_log)
#             logs.append(additional_heal_log)
#
#     # 3. diffs 생성
#     if consumed_potion and effect_value > 0:
#         total_healing = effect_value + additional_heal_point
#         target_portion = next(
#             (
#                 rel
#                 for rel in state.request.relations
#                 if rel.type == RelationType.CONSUME
#                 and consumed_potion["item_id"] == rel.effect_entity_id
#             ),
#             None,
#         )
#
#         if target_portion is not None:
#             player_diff = EntityDiff(
#                 state_entity_id=player_id, diff={"hp": total_healing}
#             )
#             diffs.append(player_diff)
#             rule(f"diffs.append({player_diff.model_dump()})")
#
#             consumed_potion_rel = UpdateRelation(
#                 cause_entity_id=player_id,
#                 effect_entity_id=target_portion.effect_entity_id,
#                 type=RelationType.CONSUME,
#                 quantity=-1,
#             )
#
#             relations.append(consumed_potion_rel)
#             rule(f"relations.append({consumed_potion_rel.model_dump()})")
#
#         rule(f"[치유 계산] 포션 기본 회복량: {effect_value}")
#         logs.append(f"[치유 계산] 포션 기본 회복량: {effect_value}")
#
#         if additional_heal_point > 0:
#             rule(f"[치유 계산] 주사위 추가 회복량: {additional_heal_point}")
#             logs.append(f"[치유 계산] 주사위 추가 회복량: {additional_heal_point}")
#
#         rule(f"[치유 계산] 총 치유량: {total_healing}")
#         logs.append(f"[치유 계산] 총 치유량: {total_healing}")
#
#     return {
#         "diffs": diffs,
#         "relations": relations,
#         "is_success": is_success,
#         "logs": logs,
#     }
#
#
# async def unknown_node(state: PlaySessionState) -> Dict[str, Any]:
#     logs = state.logs[:]
#     diffs = state.diffs[:]
#     relations = state.relations[:]
#
#     gm_service: GmService = state.gm_service
#
#     dice = await gm_service.rolling_dice(2, 6)
#     dice_result_log = f"이해할 수 없는 행동... {dice.message}{' | 잭팟!!' if dice.is_critical_success else ''} | 굴림값 {dice.roll_result} + 능력보정치 {dice.ability_score} = 총합 {dice.total}"
#     rule(dice_result_log)
#     logs.append(dice_result_log)
#
#     return {
#         "diffs": diffs,
#         "relations": relations,
#         "is_success": dice.is_success,
#         "logs": logs,
#     }
