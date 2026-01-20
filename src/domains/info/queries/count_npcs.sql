-- name: count_npcs
SELECT COUNT(*) FROM npcs
WHERE (%(npc_ids)s IS NULL OR npc_id = ANY(%(npc_ids)s));
