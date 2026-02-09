from domains.session.dtos.session_dtos import SessionRequest
from domains.session.session_service import SessionService


class _NoUserSessionsCursor:
    def __init__(self):
        self.connection = self

    def execute(self, *_args, **_kwargs):
        raise Exception('relation "user_sessions" does not exist')

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def commit(self):
        return None


async def test_get_user_sessions_missing_table_returns_empty():
    svc = SessionService(_NoUserSessionsCursor())
    sessions, meta = await svc.get_user_sessions(user_id=1, skip=0, limit=10)

    assert sessions == []
    assert meta.total_count == 0
    assert meta.skip == 0
    assert meta.limit == 10


async def test_add_user_session_missing_table_noop():
    svc = SessionService(_NoUserSessionsCursor())
    req = SessionRequest(user_id=1, session_id="sess-1")

    out = await svc.add_user_session(req)

    assert out.user_id == 1
    assert out.session_id == "sess-1"


async def test_del_user_session_missing_table_noop():
    svc = SessionService(_NoUserSessionsCursor())
    req = SessionRequest(user_id=1, session_id="sess-2")

    out = await svc.del_user_session(req)

    assert out == "sess-2"
