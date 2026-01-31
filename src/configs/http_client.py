import httpx


class HttpClientHolder:
    client: httpx.AsyncClient = None

http_holder = HttpClientHolder()