-- name: create_user
INSERT INTO users (username, password_hash, email)
VALUES (%s, %s, %s)
RETURNING user_id, username, email, created_at;
