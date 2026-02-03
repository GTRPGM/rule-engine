import httpx
from fastapi import HTTPException, status

from common.dtos.proxy_service_dto import ProxyService
from configs.http_client import http_holder
from configs.setting import (
    SCENARIO_SERVICE_HOST,
    SCENARIO_SERVICE_PORT,
    STATE_MANAGER_HOST,
    STATE_MANAGER_PORT,
)


async def proxy_request(
    method: str,
    path: str,
    # token: str,
    params=None,
    json=None,
    provider: ProxyService = ProxyService.STATE_MANAGER,
) -> dict:
    """마이크로서비스로 요청을 전달하는 공통 비동기 메서드"""
    if provider == ProxyService.STATE_MANAGER:
        target_host = STATE_MANAGER_HOST
        target_port = STATE_MANAGER_PORT
    else:
        target_host = SCENARIO_SERVICE_HOST
        target_port = SCENARIO_SERVICE_PORT

    url = f"http://{target_host}:{target_port}{path}"
    client = http_holder.client

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HTTP 클라이언트가 초기화되지 않았습니다."
        )

    try:
        response = await client.request(
            method=method,
            url=url,
            params=params,
            json=json,
        )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Remote Service Error"),
            )
        return response.json()

    except httpx.RequestError as e:
        # 네트워크/DNS 오류 등
        if "Temporary failure in name resolution" in str(e):
            import asyncio
            await asyncio.sleep(0.5) # 짧은 대기 후 재시도 기회 제공 (실제 재시도는 상위 레벨에서 처리 권장하지만, 로그 명확화)
        
        error_msg = f"마이크로서비스 연결 실패: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=error_msg
        )
