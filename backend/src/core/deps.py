from fastapi import Depends, HTTPException, Request
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.services.match import MatchService
from src.services.action import ActionService
from src.models.user import User
from src.db.session import get_db
from src.services.user import UserService
from src.services.profile import ProfileService

async def get_user_service(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return UserService(db)

async def get_profile_service(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return ProfileService(db)

async def get_action_service(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return ActionService(db)

async def get_match_service(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return MatchService(db)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
ActionServiceDep = Annotated[ActionService, Depends(get_action_service)]
MatchServiceDep = Annotated[MatchService, Depends(get_match_service)]

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    telegram_id = request.headers.get("X-Telegram-ID")
    
    if not telegram_id:
        raise HTTPException(status_code=401, detail="X-Telegram-ID header required")
    
    result = await db.execute(
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(selectinload(User.profile))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not registered")
    
    return user

CurrentUserDep = Annotated[User, Depends(get_current_user)]