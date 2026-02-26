import logging
import httpx
from typing import Optional
from src.config import settings
import asyncio
from functools import wraps
from httpx import HTTPStatusError

logger = logging.getLogger(__name__)

def retry_on_http_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except HTTPStatusError as e:
                    if e.response.status_code >= 500 and attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
                        continue
                    raise
            return None
        return wrapper
    return decorator

class BackendClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
    
    def _headers(self, telegram_id: int) -> dict:
        return {
            "X-Telegram-ID": str(telegram_id),
            "Content-Type": "application/json"
        }
    
    @retry_on_http_error()
    async def register_user(self, telegram_id: int, username: str = None, first_name: str = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/users/register",
                json={"telegram_id": str(telegram_id), "username": username, "first_name": first_name}
            )
            response.raise_for_status()
            return response.json()
    
    @retry_on_http_error()
    async def get_profile(self, telegram_id: int) -> Optional[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/profile",
                headers=self._headers(telegram_id)
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    
    @retry_on_http_error()
    async def create_profile(self, telegram_id: int, profile_data: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/profile",
                json=profile_data,
                headers=self._headers(telegram_id)
            )
            response.raise_for_status()
            return response.json()
    
    @retry_on_http_error()
    async def update_profile(self, telegram_id: int, profile_data: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}/profile",
                json=profile_data,
                headers=self._headers(telegram_id)
            )
            response.raise_for_status()
            return response.json()
    
    @retry_on_http_error()
    async def get_next_profile(self, telegram_id: int) -> Optional[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:                
            response = await client.get(
                f"{self.base_url}/profile/next",
                headers=self._headers(telegram_id)
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    
    @retry_on_http_error()
    async def send_action(
        self, 
        telegram_id: int,
        to_user_id: int,
        action_type: str,
        report_reason: str = None
    ) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            json_data = {"to_user_id": to_user_id, "action_type": action_type}
            if report_reason:
                json_data["report_reason"] = report_reason
            response = await client.post(
                f"{self.base_url}/actions",
                json=json_data,
                headers=self._headers(telegram_id)
            )
            logger.info(response.text)
            logger.info(response.status_code)
            response.raise_for_status()
    
    @retry_on_http_error()
    async def get_next_incoming_like(self, telegram_id: int) -> Optional[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:            
            response = await client.get(
                f"{self.base_url}/matches/incoming/next",
                headers=self._headers(telegram_id)
            )
            
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    
    @retry_on_http_error()
    async def decide_on_incoming(self, telegram_id: int, target_user_id: int, action_type: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/matches/incoming/{target_user_id}/decide",
                json={
                    "to_user_id": target_user_id,
                    "action_type": action_type
                },
                headers=self._headers(telegram_id)
            )
            response.raise_for_status()

backend_client = BackendClient(settings.BACKEND_URL)