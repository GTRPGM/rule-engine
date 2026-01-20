INSERT INTO npc_inventories (
    npc_id,
    item_id,
    base_price,
    is_infinite_stock
) VALUES (
    %(npc_id)s,
    %(item_id)s,
    %(base_price)s,
    %(is_infinite_stock)s
) RETURNING inventory_id;