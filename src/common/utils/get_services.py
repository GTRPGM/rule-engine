from fastapi.params import Depends

from configs.database import get_db_cursor
from domains.info.enemy_service import EnemyService
from src.domains.info.item_service import ItemService


def get_item_service(cursor=Depends(get_db_cursor)):
    return ItemService(cursor)


def get_enemy_service(cursor=Depends(get_db_cursor)):
    return EnemyService(cursor)
