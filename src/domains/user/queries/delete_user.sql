UPDATE users
SET is_active = false
WHERE user_id = %s
RETURNING user_id;
