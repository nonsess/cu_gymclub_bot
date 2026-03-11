import pytest
from unittest.mock import AsyncMock
from src.models.profile import GenderEnum


@pytest.mark.asyncio
async def test_create_profile_success(client, session):
    from src.repositories.user import UserRepository

    user_repo = UserRepository(session)
    await user_repo.create(
        telegram_id="123456789",
        username="@testuser",
        first_name="Test"
    )
    
    response = await client.post(
        "/profile",
        json={
            "name": "Алексей",
            "description": "Люблю тренироваться каждый день в зале",
            "gender": "male",
            "age": 25,
            "media": []
        },
        headers={"X-Telegram-ID": "123456789"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Алексей"
    assert data["age"] == 25
    assert "id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_create_profile_already_exists(client, session):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository

    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user = await user_repo.create(telegram_id="111222333", username="@existing")
    await profile_repo.create(
        user_id=user.id,
        name="Existing",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.female,
        age=22
    )
    
    response = await client.post(
        "/profile",
        json={
            "name": "Duplicate",
            "description": "Люблю тренироваться каждый день в зале",
            "gender": "male",
            "age": 25,
            "media": []
        },
        headers={"X-Telegram-ID": "111222333"}
    )
    
    assert response.status_code in [400, 409]


@pytest.mark.asyncio
async def test_create_profile_validation_error(client, session):
    from src.repositories.user import UserRepository

    user_repo = UserRepository(session)
    await user_repo.create(telegram_id="444555666", username="@short")
    
    response = await client.post(
        "/profile",
        json={
            "name": "Test",
            "description": "Коротко",
            "gender": "male",
            "age": 25,
            "media": []
        },
        headers={"X-Telegram-ID": "444555666"}
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_profile_user_not_found(client):
    response = await client.post(
        "/profile",
        json={
            "name": "Test",
            "description": "Люблю тренироваться каждый день в зале",
            "gender": "male",
            "age": 25,
            "media": []
        },
        headers={"X-Telegram-ID": "999999999"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_success(client, session):    
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user = await user_repo.create(telegram_id="999888777", username="@test")
    await profile_repo.create(
        user_id=user.id,
        name="Test User",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25
    )
    
    response = await client.get(
        "/profile",
        headers={"X-Telegram-ID": "999888777"}
    )
    
    assert response.status_code == 200
    assert response.json()["name"] == "Test User"


@pytest.mark.asyncio
async def test_get_profile_not_found(client, session):
    from src.repositories.user import UserRepository

    user_repo = UserRepository(session)
    await user_repo.create(telegram_id="777888999", username="@no_profile")
    
    response = await client.get(
        "/profile",
        headers={"X-Telegram-ID": "777888999"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_profile_no_header(client):
    response = await client.get("/profile")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile_success(client, session):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user = await user_repo.create(telegram_id="101010101", username="@updatable")
    await profile_repo.create(
        user_id=user.id,
        name="Old Name",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.female,
        age=20
    )
    
    response = await client.patch(
        "/profile",
        json={
            "name": "New Name",
            "age": 30,
            "description": "Новое описание профиля для тестирования обновлений"
        },
        headers={"X-Telegram-ID": "101010101"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["age"] == 30
    assert data["description"] == "Новое описание профиля для тестирования обновлений"


@pytest.mark.asyncio
async def test_update_profile_partial(client, session, mock_cache):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user = await user_repo.create(telegram_id="202020202", username="@partial")
    await profile_repo.create(
        user_id=user.id,
        name="Partial",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25
    )
    
    mock_cache['profile'].invalidate_profile = AsyncMock()
    
    response = await client.patch(
        "/profile",
        json={"age": 26},
        headers={"X-Telegram-ID": "202020202"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 26
    assert data["name"] == "Partial"

@pytest.mark.asyncio
async def test_update_profile_not_found(client, session):
    from src.repositories.user import UserRepository

    user_repo = UserRepository(session)
    await user_repo.create(telegram_id="303030303", username="@no_profile_patch")
    
    response = await client.patch(
        "/profile",
        json={"name": "New"},
        headers={"X-Telegram-ID": "303030303"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_profile_validation_error(client, session):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user = await user_repo.create(telegram_id="404040404", username="@invalid")
    await profile_repo.create(
        user_id=user.id,
        name="Valid",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.female,
        age=25
    )
    
    response = await client.patch(
        "/profile",
        json={"description": "Коротко"},
        headers={"X-Telegram-ID": "404040404"}
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_next_profile_success(client, session, mock_cache):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    current_user = await user_repo.create(telegram_id="505050505", username="@swiper")
    await profile_repo.create(
        user_id=current_user.id,
        name="Current",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25,
        embedding=[0.1] * 384
    )
    
    for i in range(3):
        user = await user_repo.create(telegram_id=f"50505050{i}", username=f"@swipeable{i}")
        await profile_repo.create(
            user_id=user.id,
            name=f"Swipeable {i}",
            description="Люблю тренироваться каждый день в зале",
            gender=GenderEnum.female,
            age=20 + i,
            embedding=[0.1 + i*0.01] * 384
        )
    
    mock_cache['profile'].pop_from_queue = AsyncMock(return_value=None)
    mock_cache['profile'].get_seen_user_ids = AsyncMock(return_value=[])
    mock_cache['profile'].fill_queue = AsyncMock()
    mock_cache['profile'].cache_profile = AsyncMock()
    mock_cache['profile'].add_seen_user_id = AsyncMock()
    
    response = await client.get(
        "/profile/next",
        headers={"X-Telegram-ID": "505050505"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "id" in data
    assert data["name"] != "Current"


@pytest.mark.asyncio
async def test_get_next_profile_no_more_profiles(client, session, mock_cache):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    current_user = await user_repo.create(telegram_id="606060606", username="@lonely")
    await profile_repo.create(
        user_id=current_user.id,
        name="Lonely",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25,
        embedding=[0.5] * 384
    )
    
    mock_cache['profile'].pop_from_queue = AsyncMock(return_value=None)
    mock_cache['profile'].get_seen_user_ids = AsyncMock(return_value=[])

    response = await client.get(
        "/profile/next",
        headers={"X-Telegram-ID": "606060606"}
    )
    
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_next_profile_user_has_no_profile(client, session, mock_cache):
    from src.repositories.user import UserRepository

    user_repo = UserRepository(session)
    
    await user_repo.create(telegram_id="707070707", username="@no_profile_next")
    
    mock_cache['profile'].pop_from_queue = AsyncMock(return_value=None)
    mock_cache['profile'].get_seen_user_ids = AsyncMock(return_value=[])
    
    response = await client.get(
        "/profile/next",
        headers={"X-Telegram-ID": "707070707"}
    )
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_next_profile_excludes_seen(client, session, mock_cache):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    current_user = await user_repo.create(telegram_id="808080808", username="@seen_test")
    await profile_repo.create(
        user_id=current_user.id,
        name="Current",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25,
        embedding=[0.2] * 384
    )
    
    user1 = await user_repo.create(telegram_id="808080801", username="@seen1")
    profile1 = await profile_repo.create(
        user_id=user1.id,
        name="Seen User 1",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.female,
        age=22,
        embedding=[0.2] * 384
    )
    
    user2 = await user_repo.create(telegram_id="808080802", username="@seen2")
    profile2 = await profile_repo.create(
        user_id=user2.id,
        name="Seen User 2",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.female,
        age=23,
        embedding=[0.2] * 384
    )
    
    mock_cache['profile'].add_seen_user_id = AsyncMock()
    mock_cache['profile'].pop_from_queue = AsyncMock(return_value=None)
    mock_cache['profile'].get_seen_user_ids = AsyncMock(return_value=[user1.id])
    
    response = await client.get(
        "/profile/next",
        headers={"X-Telegram-ID": "808080808"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] != "Seen User 1"
