INSERT INTO npcs (
    name,
    disposition,
    occupation,
    dialogue_style,
    description,
    base_difficulty,
    combat_description
) VALUES (
    %(name)s,
    %(disposition)s,
    %(occupation)s,
    %(dialogue_style)s,
    %(description)s,
    %(base_difficulty)s,
    %(combat_description)s
) RETURNING npc_id;