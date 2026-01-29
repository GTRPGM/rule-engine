from domains.play.dtos.player_dtos import (
            FullPlayerState,
            ItemBase,
            NPCRelation,
            PlayerStateResponse,
)

dummy_player: FullPlayerState = FullPlayerState(
            player=PlayerStateResponse(
                hp=150,
                gold=800,
                items=[
                    ItemBase(item_id="28", name="안식처제 보급검", description="고대 제단의 비밀이 담긴 돌판입니다. 고고학적 가치가 높습니다.", item_type="equipment", meta={"effect_value": 15}, is_stackable=False),
                    ItemBase(item_id="29", name="모험가용 가죽 갑옷", description="활동성을 중시하여 제작된 가벼운 가죽 갑옷입니다.", item_type="equipment", meta={"effect_value": 10}, is_stackable=False),
                    ItemBase(item_id="78", name="최하급 회복 포션", description="희석된 약초 물입니다. 찰과상을 겨우 치료하는 수준입니다.", item_type="consumable", meta={"heal_amount": 10, "quantity": 3}, is_stackable=True),
                    ItemBase(item_id="79", name="하급 회복 포션", description="일반적인 모험가들이 가장 많이 사용하는 표준 회복제입니다.", item_type="consumable", meta={"heal_amount": 30, "quantity": 2}, is_stackable=True),
                    ItemBase(item_id="80", name="중급 회복 포션", description="정제된 약초 추출물이 들어있어 깊은 상처도 빠르게 아물게 합니다.", item_type="consumable", meta={"heal_amount": 80, "quantity": 1}, is_stackable=True),
                ]
            ),
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