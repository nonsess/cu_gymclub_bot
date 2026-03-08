import pytest
from src.repositories.user import UserRepository


@pytest.mark.asyncio
async def test_create_user(session):
    repo = UserRepository(session)
    
    user = await repo.create(
        telegram_id="123456789",
        username="@testuser",
        first_name="Test"
    )
    
    assert user.telegram_id == "123456789"
    assert user.username == "@testuser"
    assert user.is_banned == False


@pytest.mark.asyncio
async def test_get_by_telegram_id(session):
    repo = UserRepository(session)
    
    await repo.create(telegram_id="987654321", username="@findme")
    
    user = await repo.get_by_telegram_id("987654321")
    
    assert user is not None
    assert user.username == "@findme"


@pytest.mark.asyncio
async def test_get_by_telegram_id_not_found(session):
    repo = UserRepository(session)
    
    user = await repo.get_by_telegram_id("nonexistent")
    
    assert user is None


@pytest.mark.asyncio
async def test_create_user_with_none_fields(session):
    repo = UserRepository(session)
    
    user = await repo.create(
        telegram_id="141414141",
        username=None,
        first_name=None
    )
    
    assert user.telegram_id == "141414141"
    assert user.username is None
    assert user.first_name is None


@pytest.mark.asyncio
async def test_create_user_empty_username(session):
    repo = UserRepository(session)
    
    user = await repo.create(
        telegram_id="151515151",
        username="",
        first_name="Test"
    )
    
    assert user.username == ""

@pytest.mark.asyncio
async def test_delete_user(session):
    repo = UserRepository(session)
    
    user = await repo.create(telegram_id="131313131")
    
    await repo.delete(user)
    await session.commit()
    
    found = await repo.get_by_telegram_id("131313131")
    assert found is None

@pytest.mark.asyncio
async def test_get_by_id(session):
    from src.repositories.base import BaseRepository
    
    repo = UserRepository(session)
    user = await repo.create(telegram_id="121212121")
    
    base_repo = BaseRepository(type(user), session)
    found = await base_repo.get(user.id)
    
    assert found is not None
    assert found.telegram_id == "121212121"

@pytest.mark.asyncio
async def test_update_user_ban(session):
    repo = UserRepository(session)
    
    user = await repo.create(telegram_id="777888999", is_banned=False)
    
    await repo.update(user, is_banned=True)
    await session.refresh(user)
    
    assert user.is_banned == True


@pytest.mark.asyncio
async def test_update_user_username(session):
    repo = UserRepository(session)
    
    user = await repo.create(telegram_id="101010101", username="@old")
    
    await repo.update(user, username="@new")
    await session.refresh(user)
    
    assert user.username == "@new"


@pytest.mark.asyncio
async def test_create_if_not_exists_creates_new(session):
    repo = UserRepository(session)
    
    user = await repo.create_if_not_exists(
        telegram_id="111222333",
        username="@newuser",
        first_name="New"
    )
    
    assert user.telegram_id == "111222333"
    assert user.username == "@newuser"
    assert user.first_name == "New"


@pytest.mark.asyncio
async def test_create_if_not_exists_returns_existing(session):
    repo = UserRepository(session)
    
    user1 = await repo.create(telegram_id="444555666", username="@original")
    
    user2 = await repo.create_if_not_exists(
        telegram_id="444555666",
        username="@should_not_change",
        first_name="ShouldNotChange"
    )
    
    assert user1.id == user2.id
    assert user2.username == "@original"
    assert user2.first_name != "ShouldNotChange"