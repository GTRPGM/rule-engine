import pytest
from unittest.mock import AsyncMock, MagicMock
from domains.play.dtos.play_dtos import (
    PlaySessionState,
    PlaySceneRequest,
    EntityUnit,
    EntityType,
    RelationType,
)
from domains.play.utils.phase_nodes.dialogue_node import dialogue_node


@pytest.mark.asyncio
async def test_dialogue_creates_new_relation_on_first_meet():
    """
    검증 목표: 초기 관계가 없는 상태(relations=[])에서 NPC와 대화 시,
    룰엔진이 새로운 관계(RelationType)와 호감도 변화량을 반환하는지 확인.
    """

    # 1. Mock Data Setup
    player_id = "player-uuid-123"
    npc_id = "npc-uuid-456"

    # 요청 페이로드: 관계 없음
    request = PlaySceneRequest(
        session_id="session-1",
        scenario_id="scenario-1",
        locale_id=1,
        sequence_type="DIALOGUE",
        target="",
        entities=[
            EntityUnit(
                state_entity_id=player_id,
                entity_name="Player",
                entity_type=EntityType.PLAYER,
                phase_id=1,
            ),
            EntityUnit(
                state_entity_id=npc_id,
                entity_name="Wandering Merchant",
                entity_type=EntityType.NPC,
                phase_id=1,
            ),
        ],
        relations=[],  # 중요: 초기 관계 없음
        story="상인에게 인사를 건넨다.",
    )

    # GM Service Mock (주사위 굴림 성공 가정)
    mock_gm_service = AsyncMock()
    mock_gm_service.rolling_dice.return_value = MagicMock(
        is_success=True,
        total=15,
        roll_result=10,
        ability_score=5,
        message="주사위 성공",
    )

    state = PlaySessionState(
        request=request,
        logs=[],
        diffs=[],
        relations=[],
        current_player_id=player_id,
        player_state=MagicMock(),  # 플레이어 상태 존재 가정
        gm_service=mock_gm_service,
        # 다른 서비스들은 사용 안함
        item_service=MagicMock(),
        enemy_service=MagicMock(),
        world_service=MagicMock(),
        llm=MagicMock(),
    )

    # 2. Execute Logic
    result = await dialogue_node(state)

    # 3. Verify
    print("\n[LOGS]:", result["logs"])

    # 3-1. 관계 생성 여부 확인
    relations = result["relations"]
    assert len(relations) == 1, "새로운 관계가 생성되어야 합니다."

    new_rel = relations[0]
    print(f"[NEW RELATION]: {new_rel}")

    assert new_rel.cause_entity_id == player_id
    assert new_rel.effect_entity_id == npc_id
    # 호감도 변화량이 0이 아니어야 함 (성공했으므로 양수)
    assert new_rel.affinity_score > 0
    # 절대값이 아닌 변화량인지 확인 (기존 로직상 변화량은 주사위 차이값 등 작은 정수)
    assert new_rel.affinity_score < 50

    print("\n[SUCCESS] 초기 대화 시 관계 생성 로직 정상 동작 확인.")
