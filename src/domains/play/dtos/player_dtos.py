from typing import List, Optional

from pydantic import BaseModel


class PlayerStateResponse(BaseModel):
    hp: int
    gold: int
    items: List[int]


class NPCRelation(BaseModel):
    npc_id: str
    npc_name: Optional[str] = None
    affinity_score: int


class FullPlayerState(BaseModel):
    player: PlayerStateResponse
    player_npc_relations: List[NPCRelation] = []
