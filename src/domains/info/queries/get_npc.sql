SELECT
    n.*,
    (
        SELECT json_agg(
            json_build_object(
                'inventory_id', ni.inventory_id,
                'item_id', ni.item_id,
                'base_price', i.base_price,
                'is_infinite_stock', ni.is_infinite_stock
            )
        )
        FROM npc_inventories ni
        JOIN items i ON ni.item_id = i.item_id
        WHERE ni.npc_id = n.npc_id
    ) AS inventory_list
FROM npcs n
WHERE n.npc_id = %(npc_id)s;
