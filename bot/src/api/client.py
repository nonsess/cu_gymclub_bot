import logging
import httpx
from typing import Optional, List
from src.config import settings

logger = logging.getLogger(__name__)


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
    
    async def register_user(self, telegram_id: int, username: str = None, first_name: str = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/users/register",
                json={"telegram_id": str(telegram_id), "username": username, "first_name": first_name}
            )
            response.raise_for_status()
            return response.json()
    
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
    
    async def create_profile(self, telegram_id: int, profile_data: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/profile",
                json=profile_data,
                headers=self._headers(telegram_id)
            )
            response.raise_for_status()
            return response.json()
    
    async def update_profile(self, telegram_id: int, profile_data: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(
                f"{self.base_url}/profile",
                json=profile_data,
                headers=self._headers(telegram_id)
            )
            response.raise_for_status()
            return response.json()
    
    async def get_next_profile(self, telegram_id: int, seen_ids: List[int]) -> Optional[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            params = {"seen_ids": seen_ids}
            response = await client.get(
                f"{self.base_url}/profile/next",
                params=params,
                headers=self._headers(telegram_id)
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    
    async def send_action(self, telegram_id: int, to_user_id: int, action_type: str, report_reason: str = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            json_data = {"to_user_id": to_user_id, "action_type": action_type}
            if report_reason:
                json_data["report_reason"] = report_reason
            response = await client.post(
                f"{self.base_url}/actions",
                json=json_data,
                headers=self._headers(telegram_id)
            )
            response.raise_for_status()
            return response.json()
    
    async def get_incoming_likes(self, telegram_id: int) -> List[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/matches/incoming",
                headers=self._headers(telegram_id)
            )
            response.raise_for_status()
            return response.json()
    
    async def decide_on_incoming(self, telegram_id: int, target_user_id: int, action_type: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/matches/incoming/{target_user_id}/decide",
                json={"action_type": action_type},
                headers=self._headers(telegram_id)
            )
            response.raise_for_status()
            return response.json()
    
    async def get_matches(self, telegram_id: int) -> List[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/matches",
                headers=self._headers(telegram_id)
            )
            response.raise_for_status()
            return response.json()

backend_client = BackendClient(settings.BACKEND_URL)