from domains.play.dtos.play_dtos import PhaseType
from domains.play.utils.phase_handler import (
    CombatHandler,
    DialogueHandler,
    ExplorationHandler,
    RestHandler,
    UnknownHandler,
)


class PhaseHandlerFactory:
    _handlers = {
        PhaseType.COMBAT: CombatHandler(),
        PhaseType.EXPLORATION: ExplorationHandler(),
        PhaseType.DIALOGUE: DialogueHandler(),
        PhaseType.REST: RestHandler(),
        PhaseType.UNKNOWN: UnknownHandler(),
    }

    @classmethod
    def get_handler(cls, phase_type: PhaseType):
        return cls._handlers.get(phase_type, cls._handlers[PhaseType.UNKNOWN])
