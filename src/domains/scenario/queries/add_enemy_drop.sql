INSERT INTO enemy_drops (
    enemy_id,
    item_id,
    drop_rate,
    min_quantity,
    max_quantity
) VALUES (
    %(enemy_id)s,
    %(item_id)s,
    %(drop_rate)s,
    %(min_quantity)s,
    %(max_quantity)s
) RETURNING drop_id;