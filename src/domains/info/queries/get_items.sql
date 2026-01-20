-- name: get_items
-- 아이템 목록 조회 및 필터링
SELECT * FROM items
WHERE (%(item_ids)s IS NULL OR item_id = ANY(%(item_ids)s))
ORDER BY item_id ASC
LIMIT %(limit)s OFFSET %(skip)s;
