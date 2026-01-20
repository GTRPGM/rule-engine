-- name: count_enemies
-- 전체 개수 조회 (페이지네이션 계산용)
SELECT COUNT(*) FROM enemies
WHERE (%(enemy_ids)s IS NULL OR enemy_id = ANY(%(enemy_ids)s));
