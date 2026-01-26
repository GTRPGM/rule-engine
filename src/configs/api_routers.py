from domains.info.info_router import info_router
from domains.play.play_router import play_router
from domains.scenario.scenario_router import scenario_router

API_ROUTERS = [
    play_router,
    info_router,
    scenario_router,
]
