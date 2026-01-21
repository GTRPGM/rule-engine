from domains.play.dtos.play_dtos import (
    PlaySceneRequest,
    PlaySceneResponse,
    PlaySceneUpdate,
)


class PlayService:
    def __init__(self, cursor):
        self.cursor = cursor

    async def play_scene(self, request: PlaySceneRequest) -> PlaySceneResponse:
        print(request)

        updates = [
            PlaySceneUpdate(
                entity_id=1,
                entity_attribute={"hp": -10},
                entity_relation={"target_entity_id": 1, "update_relation": "relation"},
            )
        ]

        return PlaySceneResponse(
            session_id=request.session_id,
            scenario_id=request.scenario_id,
            update=updates,
        )
