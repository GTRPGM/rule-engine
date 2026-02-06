UPDATE users
SET password_hash = COALESCE(%(password_hash)s, password_hash)
WHERE user_id = %(user_id)s
RETURNING user_id;
