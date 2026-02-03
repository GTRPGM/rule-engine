-- name: get_sessions
SELECT
    user_id,
    session_id,
    created_at
FROM user_sessions
WHERE user_id = %(user_id)s
  AND is_deleted = %(is_deleted)s
ORDER BY session_id ASC
LIMIT %(limit)s OFFSET %(skip)s;