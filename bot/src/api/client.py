import logging
import httpx
from typing import Optional
from src.config import settings

logger = logging.getLogger(__name__)

class BackendClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            )
        )
        
    def _headers(self, telegram_id: int) -> dict:
        return {
            "X-Telegram-ID": str(telegram_id),
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, telegram_id: int, **kwargs) -> Optional[dict]:
        response = await self._client.request(
            method, 
            endpoint, 
            headers=self._headers(telegram_id), 
            **kwargs
        )
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        return response.json() if response.content else {}

    async def register_user(
        self,
        telegram_id: int,
        username: str = None,
        first_name: str = None
    ) -> dict:
        data = {
            "telegram_id": str(telegram_id),
            "username": username,
            "first_name": first_name
        }

        response = await self._client.post("/users/register", json=data)
        
        response.raise_for_status()
        return response.json()
    
    async def get_profile(self, telegram_id: int) -> Optional[dict]:
        return await self._request("GET", "/profile", telegram_id)
    
    async def create_profile(self, telegram_id: int, profile_data: dict) -> dict:
        return await self._request("POST", "/profile", telegram_id, json=profile_data)
    
    async def update_profile(self, telegram_id: int, profile_data: dict) -> dict:
        return await self._request("PATCH", "/profile", telegram_id, json=profile_data)
    
    async def get_next_profile(self, telegram_id: int) -> Optional[dict]:
        return await self._request("GET", "/profile/next", telegram_id)
    
    async def send_action(
        self, 
        telegram_id: int,
        to_user_id: int,
        action_type: str,
        report_reason: str = None
    ) -> dict:
        json_data = {"to_user_id": to_user_id, "action_type": action_type}
        
        if report_reason:
            json_data["report_reason"] = report_reason
        
        return await self._request("POST", "/actions", telegram_id, json=json_data)
    
    async def get_next_incoming_like(self, telegram_id: int) -> Optional[dict]:
        return await self._request("GET", "/matches/incoming/next", telegram_id)
    
    async def decide_on_incoming(
        self, 
        telegram_id: int, 
        action_id: int, 
        decision: str,
        report_reason: str = None
    ) -> dict:
        json_data = {
            "action_id": action_id,
            "decision": decision
        }
        
        if report_reason:
            json_data["report_reason"] = report_reason
        
        return await self._request("POST", "/matches/incoming/decide", telegram_id, json=json_data)

    async def start_broadcast(self, telegram_id: int, message_text: str) -> dict:
        return await self._request(
            "POST",
            "/admin/broadcasts",
            telegram_id,
            params={"message_text": message_text}
        )

    async def export_profiles(
        self,
        telegram_id: int,
        params: dict = None
    ) -> str:
        response = await self._client.get(
            "/admin/export/profiles",
            headers=self._headers(telegram_id),
            params=params
        )
        
        response.raise_for_status()
        return response.text
    
    async def ban_user(self, telegram_id: int, user_id: int) -> None:
        await self._client.post(
            f"/admin/ban/user/{user_id}",
            headers=self._headers(telegram_id)
        )

backend_client = BackendClient(settings.BACKEND_URL)