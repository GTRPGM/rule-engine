-- name: get_sessions
SELECT
    user_id,
    session_id,
    created_at
FROM user_sessions
WHERE user_id = %(user_id)s
  -- is_deleted가 True이면 뒤의 조건과 상관없이 항상 참(전체 조회)
  -- is_deleted가 False이면 실제 컬럼의 is_deleted = False인 것만 조회
  AND (%(is_deleted)s IS TRUE OR is_deleted = FALSE)
ORDER BY session_id ASC
LIMIT %(limit)s OFFSET %(skip)s;
