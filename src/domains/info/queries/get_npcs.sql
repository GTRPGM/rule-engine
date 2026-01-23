SELECT * FROM npcs
WHERE (%(npc_ids)s IS NULL OR npc_id = ANY(%(npc_ids)s))
ORDER BY npc_id ASC
LIMIT %(limit)s OFFSET %(skip)s;
