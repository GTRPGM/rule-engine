-- name: count_personalities
-- 전체 개수 조회 (페이지네이션 계산용)
SELECT COUNT(*) FROM personality
WHERE (%(personality_ids)s IS NULL OR id = ANY(%(personality_ids)s));
