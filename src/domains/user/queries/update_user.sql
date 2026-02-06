UPDATE users
SET
    username = COALESCE(%(username)s, username),
    email = COALESCE(%(email)s, email)
WHERE user_id = %(user_id)s
RETURNING user_id, username, email, created_at;
