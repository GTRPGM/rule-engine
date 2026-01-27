INSERT INTO npc_inventories (
    npc_id,
    item_id,
    is_infinite_stock
) VALUES (
    %(npc_id)s,
    %(item_id)s,
    %(is_infinite_stock)s
) RETURNING inventory_id;
