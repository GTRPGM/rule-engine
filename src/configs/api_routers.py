from domains.gm.gm_router import gm_router
from domains.info.info_router import info_router
from domains.scenario.scenario_router import scenario_router

API_ROUTERS = [
    gm_router,
    info_router,
    scenario_router,
]
