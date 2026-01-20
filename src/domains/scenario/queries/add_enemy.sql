INSERT INTO enemies (
    name,
    base_difficulty,
    description,
    type
) VALUES (
    %(name)s,
    %(base_difficulty)s,
    %(description)s,
    %(type)s
) RETURNING enemy_id;