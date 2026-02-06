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

    return {"세계 정보": world_data, "logs": logs}
