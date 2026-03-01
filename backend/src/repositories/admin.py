import io
import csv
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.profile import Profile

class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.__session = session

    async def export_profiles_to_csv(
        self,
        limit: int = 1000,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> str:
        query = (
            select(Profile, User)
            .join(User, Profile.user_id == User.id)
            .order_by(Profile.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        if is_active is not None:
            query = query.where(Profile.is_active == is_active)
        
        result = await self.__session.execute(query)
        rows = result.all()
        
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        writer.writerow([
            'profile_id',
            'user_id',
            'telegram_id',
            'username',
            'first_name',
            'name',
            'gender',
            'age',
            'description',
            'photo_count',
            'is_active',
            'created_at',
            'updated_at',
        ])
        
        for profile, user in rows:
            writer.writerow([
                profile.id,
                profile.user_id,
                user.telegram_id,
                user.username or '',
                user.first_name or '',
                profile.name or '',
                profile.gender.value if profile.gender else '',
                profile.age or '',
                profile.description or '',
                len(profile.photo_ids) if profile.photo_ids else 0,
                profile.is_active,
                profile.created_at.isoformat() if profile.created_at else '',
                profile.updated_at.isoformat() if profile.updated_at else '',
            ])
        
        return output.getvalue()
