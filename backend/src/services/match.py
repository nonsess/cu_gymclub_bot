from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.match import MatchRepository
from src.repositories.user import UserRepository
from src.repositories.profile import ProfileRepository
from src.core.exceptions.match import MatchNotFoundException
from src.core.exceptions.user import UserNotFoundException


class MatchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.match_repo = MatchRepository(session)
        self.user_repo = UserRepository(session)
        self.profile_repo = ProfileRepository(session)

    async def get_matches(self, user_id: int) -> list[dict]:
        matches = await self.match_repo.get_user_matches(user_id)
        
        result = []
        for match in matches:
            matched_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
            
            matched_user = await self.user_repo.get(matched_user_id)
            matched_profile = await self.profile_repo.get_by_user_id(matched_user_id)
            
            result.append({
                "match": match,
                "matched_user": matched_user,
                "matched_profile": matched_profile
            })
        
        return result

    async def get_match_detail(self, match_id: int, user_id: int) -> dict:
        match = await self.match_repo.get(match_id)
        
        if not match:
            raise MatchNotFoundException(match_id)
        
        if match.user1_id != user_id and match.user2_id != user_id:
            raise MatchNotFoundException(match_id)
        
        matched_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
        
        matched_user = await self.user_repo.get(matched_user_id)
        matched_profile = await self.profile_repo.get_by_user_id(matched_user_id)
        
        return {
            "match": match,
            "matched_user": matched_user,
            "matched_profile": matched_profile
        }

    async def get_match_contact(self, match_id: int, user_id: int) -> dict:
        detail = await self.get_match_detail(match_id, user_id)
        matched_user = detail["matched_user"]
        
        if not matched_user:
            raise UserNotFoundException(user_id=detail["match"].user2_id)
        
        if matched_user.username:
            link = f"https://t.me/{matched_user.username}"
        else:
            link = f"tg://user?id={matched_user.telegram_id}"
        
        return {
            "telegram_id": matched_user.telegram_id,
            "username": matched_user.username,
            "first_name": matched_user.first_name,
            "link": link
        }

    async def delete_match(self, match_id: int, user_id: int) -> bool:
        match = await self.match_repo.get(match_id)
        
        if not match:
            raise MatchNotFoundException(match_id)

        if match.user1_id != user_id and match.user2_id != user_id:
            raise MatchNotFoundException(match_id)
        
        await self.match_repo.delete(match)
        return True