from fastapi.params import Depends

from configs.database import get_db_cursor
from domains.info.enemy_service import EnemyService
from domains.info.npc_service import NpcService
from domains.info.world_service import WorldService
from src.domains.info.item_service import ItemService
from src.domains.info.personality_service import PersonalityService


def get_item_service(cursor=Depends(get_db_cursor)):
    return ItemService(cursor)


def get_enemy_service(cursor=Depends(get_db_cursor)):
    return EnemyService(cursor)


def get_npc_service(cursor=Depends(get_db_cursor)):
    return NpcService(cursor)


def get_personality_service(cursor=Depends(get_db_cursor)):
    return PersonalityService(cursor)


def get_world_service(cursor=Depends(get_db_cursor)):
    return WorldService(cursor)