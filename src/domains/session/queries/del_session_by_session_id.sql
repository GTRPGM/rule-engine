UPDATE user_sessions
SET
    is_deleted = true,
    deleted_at = CURRENT_TIMESTAMP
WHERE
    session_id = %(session_id)s
    AND is_deleted = false; -- 이미 삭제된 데이터는 건드리지 않음