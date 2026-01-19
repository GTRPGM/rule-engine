-- name: get_user_by_id
SELECT user_id, username, email, is_active, created_at
FROM users
WHERE user_id = %s;
