SELECT
    e.enemy_id,
    e.name,
    e.base_difficulty,
    e.description,
    e.type,
    e.created_at,
    COALESCE(
        (SELECT json_agg(
            json_build_object(
                'drop_id', ed.drop_id,
                'item_id', i.item_id,
                'item_name', i.name,
                'item_type', i.type,
                'drop_rate', ed.drop_rate,
                'min_quantity', ed.min_quantity,
                'max_quantity', ed.max_quantity,
                'grade', i.grade
            )
        )
        FROM enemy_drops ed
        JOIN items i ON ed.item_id = i.item_id
        WHERE ed.enemy_id = e.enemy_id),
        '[]'::json
    ) AS drops
FROM enemies e
WHERE e.enemy_id = %(enemy_id)s;
