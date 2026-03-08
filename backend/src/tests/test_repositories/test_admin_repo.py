import pytest
import csv
import io
from src.repositories.admin import AdminRepository
from src.repositories.user import UserRepository
from src.repositories.profile import ProfileRepository
from src.models.profile import GenderEnum


@pytest.mark.asyncio
async def test_export_profiles_to_csv_basic(session):
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    for i in range(3):
        user = await user_repo.create(
            telegram_id=f"admin{i}",
            username=f"@user{i}",
            first_name=f"User{i}"
        )
        await profile_repo.create(
            user_id=user.id,
            name=f"Profile{i}",
            description=f"Desc{i}",
            gender=GenderEnum.male,
            age=20+i
        )
    
    repo = AdminRepository(session)
    csv_content = await repo.export_profiles_to_csv(limit=10, offset=0)
    
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    assert len(rows) >= 4
    assert "profile_id" in rows[0]
    assert "telegram_id" in rows[0]


@pytest.mark.asyncio
async def test_export_profiles_filter_active(session):
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user1 = await user_repo.create(telegram_id="active1")
    await profile_repo.create(
        user_id=user1.id,
        name="Active",
        description="Desc",
        gender=GenderEnum.female,
        is_active=True
    )
    
    user2 = await user_repo.create(telegram_id="inactive1")
    await profile_repo.create(
        user_id=user2.id,
        name="Inactive",
        description="Desc",
        gender=GenderEnum.male,
        is_active=False
    )
    
    repo = AdminRepository(session)
    
    csv_active = await repo.export_profiles_to_csv(limit=10, is_active=True)
    assert "Active" in csv_active
    assert "Inactive" not in csv_active
    
    csv_inactive = await repo.export_profiles_to_csv(limit=10, is_active=False)
    assert "Inactive" in csv_inactive
    assert "Active" not in csv_inactive


@pytest.mark.asyncio
async def test_export_profiles_pagination(session):
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    for i in range(5):
        user = await user_repo.create(telegram_id=f"page{i}")
        await profile_repo.create(
            user_id=user.id,
            name=f"Page{i}",
            description="Desc",
            gender=GenderEnum.female
        )
    
    repo = AdminRepository(session)
    
    csv_page1 = await repo.export_profiles_to_csv(limit=2, offset=0)
    rows1 = csv_page1.strip().split('\n')
    assert len(rows1) == 3
    
    csv_page2 = await repo.export_profiles_to_csv(limit=2, offset=2)
    rows2 = csv_page2.strip().split('\n')
    assert len(rows2) == 3
    
    assert rows1[1] != rows2[1]