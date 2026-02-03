--name: insert_session
INSERT INTO user_sessions (user_id, session_id)
VALUES (%(user_id)s, %(session_id)s);