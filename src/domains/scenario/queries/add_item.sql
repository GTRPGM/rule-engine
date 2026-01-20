INSERT INTO items (
    name,
    type,
    effect_value,
    description,
    weight,
    grade,
    base_price
) VALUES (
    %(name)s,
    %(type)s,
    %(effect_value)s,
    %(description)s,
    %(weight)s,
    %(grade)s,
    %(base_price)s
) RETURNING item_id;