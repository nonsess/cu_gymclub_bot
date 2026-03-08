import pytest
from src.repositories.profile import ProfileRepository
from src.repositories.user import UserRepository
from src.models.profile import GenderEnum


@pytest.mark.asyncio
async def test_create_profile(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id="111111", username="@test")
    
    repo = ProfileRepository(session)
    profile = await repo.create(
        user_id=user.id,
        name="Алексей",
        description="Люблю тренироваться",
        gender=GenderEnum.male,
        age=25
    )
    
    assert profile.user_id == user.id
    assert profile.name == "Алексей"
    assert profile.age == 25
    assert profile.is_active == True


@pytest.mark.asyncio
async def test_get_by_user_id(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id="222222")
    
    repo = ProfileRepository(session)
    await repo.create(
        user_id=user.id,
        name="Мария",
        description="Кроссфит",
        gender=GenderEnum.female
    )
    
    profile = await repo.get_by_user_id(user.id)
    
    assert profile is not None
    assert profile.name == "Мария"


@pytest.mark.asyncio
async def test_get_by_user_id_not_found(session):
    repo = ProfileRepository(session)
    profile = await repo.get_by_user_id(999999)
    assert profile is None


@pytest.mark.asyncio
async def test_update_profile(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id="333333")
    
    repo = ProfileRepository(session)
    profile = await repo.create(
        user_id=user.id,
        name="Test",
        description="Old desc",
        gender=GenderEnum.male
    )
    
    await repo.update(profile, description="New desc", age=30)
    await session.refresh(profile)
    
    assert profile.description == "New desc"
    assert profile.age == 30


@pytest.mark.asyncio
async def test_delete_profile(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id="444444")
    
    repo = ProfileRepository(session)
    profile = await repo.create(
        user_id=user.id,
        name="ToDelete",
        description="Desc",
        gender=GenderEnum.male
    )
    
    await repo.delete(profile)
    await session.commit()
    
    found = await repo.get_by_user_id(user.id)
    assert found is None


@pytest.mark.asyncio
async def test_get_similar_profiles(session):
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    current_user = await user_repo.create(telegram_id="555555")
    await profile_repo.create(
        user_id=current_user.id,
        name="Current",
        description="Test",
        gender=GenderEnum.male,
        embedding=[0.1] * 384
    )
    
    user2 = await user_repo.create(telegram_id="555556")
    await profile_repo.create(
        user_id=user2.id,
        name="Other1",
        description="Similar",
        gender=GenderEnum.female,
        embedding=[0.15] * 384
    )
    
    user3 = await user_repo.create(telegram_id="555557")
    await profile_repo.create(
        user_id=user3.id,
        name="Other2",
        description="Different",
        gender=GenderEnum.female,
        embedding=[0.9] * 384
    )
    
    similar = await profile_repo.get_similar_profiles(
        user_embedding=[0.1] * 384,
        seen_user_ids=[current_user.id],
        limit=10,
    )
    
    assert len(similar) >= 1
    assert similar[0].name in ["Other1", "Other2"]


@pytest.mark.asyncio
async def test_get_random_profiles(session):
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    for i in range(5):
        user = await user_repo.create(telegram_id=f"60000{i}")
        await profile_repo.create(
            user_id=user.id,
            name=f"Random{i}",
            description="Desc",
            gender=GenderEnum.male
        )
    
    random_profiles = await profile_repo.get_random_profiles(
        seen_user_ids=[],
        limit=3
    )
    
    assert len(random_profiles) <= 3
    assert all(p.is_active for p in random_profiles)


@pytest.mark.asyncio
async def test_get_similar_excludes_seen(session):
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    current = await user_repo.create(telegram_id="700000")
    await profile_repo.create(
        user_id=current.id,
        name="Current",
        description="Test",
        gender=GenderEnum.male,
        embedding=[0.1] * 384
    )
    
    ids = []
    for i in range(3):
        user = await user_repo.create(telegram_id=f"70000{i+1}")
        profile = await profile_repo.create(
            user_id=user.id,
            name=f"User{i}",
            description="Desc",
            gender=GenderEnum.female,
            embedding=[0.1] * 384
        )
        ids.append(user.id)
    
    similar = await profile_repo.get_similar_profiles(
        user_embedding=[0.1] * 384,
        seen_user_ids=ids[:2] + [current.id],
        limit=10,
    )
    
    assert len(similar) == 1
    assert similar[0].user_id == ids[2]