from domains.auth.auth_router import auth_router
from src.domains.gm.gm_router import gm_router

API_ROUTERS = [
    gm_router,
    auth_router,
]
