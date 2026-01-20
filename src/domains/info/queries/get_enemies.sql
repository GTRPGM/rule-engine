-- name: get_enemies
SELECT * FROM enemies
WHERE (
    %(enemy_ids)s IS NULL
    OR cardinality(%(enemy_ids)s::int[]) = 0  -- int 배열로 캐스팅
    OR enemy_id = ANY(%(enemy_ids)s::int[])   -- int 배열로 캐스팅
)
ORDER BY enemy_id ASC
LIMIT %(limit)s OFFSET %(skip)s;
