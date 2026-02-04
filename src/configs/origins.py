from configs.setting import APP_PORT, REMOTE_HOST, WEB_PORT

origins = [
    f"http://localhost:{WEB_PORT}",
    f"http://127.0.0.1:{WEB_PORT}",
    f"http://localhost:{APP_PORT}",
    f"http://127.0.0.1:{APP_PORT}",
    f"http://{REMOTE_HOST}:{APP_PORT}",
    f"http://{REMOTE_HOST}:{WEB_PORT}",
    f"http://{REMOTE_HOST}",
]
