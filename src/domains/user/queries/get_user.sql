SELECT
    id,
    created_at
FROM user
WHERE id = %(user_id)s;