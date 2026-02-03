-- name: count_sessions
-- 전체 개수 조회 (페이지네이션 계산용)
SELECT COUNT(*)
FROM user_sessions
WHERE user_id = %(user_id)s;