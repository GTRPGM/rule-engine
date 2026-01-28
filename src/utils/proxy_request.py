import httpx
from fastapi import HTTPException, status

from common.dtos.proxy_service_dto import ProxyService
from configs.setting import REMOTE_HOST, SCENARIO_SERVICE_PORT, STATE_MANAGER_PORT


async def proxy_request(
    method: str,
    path: str,
    # token: str,
    params=None,
    json=None,
    provider: ProxyService = ProxyService.STATE_MANAGER,
) -> dict:
    """마이크로서비스로 요청을 전달하는 공통 비동기 메서드"""
    target_port = (
        STATE_MANAGER_PORT
        if provider == ProxyService.STATE_MANAGER
        else SCENARIO_SERVICE_PORT
    )

    async with httpx.AsyncClient() as client:
        try:
            url = f"http://{REMOTE_HOST}:{target_port}{path}"

            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=10.0,
            )

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Remote Service Error"),
                )
            return response.json()

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"마이크로서비스 연결 실패: {exc}",
            )
