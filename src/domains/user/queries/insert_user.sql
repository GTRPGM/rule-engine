INSERT INTO users (username, password_hash, email)
VALUES (%(username)s, %(password_hash)s, %(email)s)
RETURNING user_id, username, email, created_at;
