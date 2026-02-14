import httpx
from fastapi import HTTPException, status

from configs.http_client import http_holder


async def proxy_request(
    method: str,
    base_url: str,
    path: str,
    # token: str,
    params=None,
    json=None,
) -> dict:
    """마이크로서비스로 요청을 전달하는 공통 비동기 메서드"""
    url = f"{base_url}{path}"
    client = http_holder.client

    if base_url is None or ":None" in str(base_url):
        from utils.logger import logger
        logger.error(f"❌ 잘못된 base_url 감지됨: {base_url}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서비스 URL 설정 오류: {base_url}"
        )

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
                detail=response.json().get("detail", "원격 서비스 오류"),
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
