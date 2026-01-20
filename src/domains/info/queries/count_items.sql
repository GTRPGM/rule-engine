-- name: count_items
-- 전체 개수 조회 (페이지네이션 계산용)
SELECT COUNT(*) FROM items
WHERE (%(item_ids)s IS NULL OR item_id = ANY(%(item_ids)s));
