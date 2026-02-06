from domains.info.info_router import info_router
from domains.play.play_router import play_router
from domains.scenario.scenario_router import scenario_router
from domains.session.session_router import session_router
from domains.user.user_router import user_router

API_ROUTERS = [
    user_router,
    session_router,
    play_router,
    info_router,
    scenario_router,
]
