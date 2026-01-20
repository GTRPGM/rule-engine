-- name: get_personalities
SELECT * FROM personality
WHERE (
    %(personality_ids)s IS NULL
    OR cardinality(%(personality_ids)s::text[]) = 0  -- text 배열로 캐스팅
    OR id = ANY(%(personality_ids)s::text[])   -- text 배열로 캐스팅
)
ORDER BY id ASC
LIMIT %(limit)s OFFSET %(skip)s;
