import pytest
from src.models.profile import GenderEnum
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_send_action_success(client, session, mock_cache):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user1 = await user_repo.create(telegram_id="act_user1", username="@user1")
    user2 = await user_repo.create(telegram_id="act_user2", username="@user2")
    
    await profile_repo.create(
        user_id=user1.id,
        name="User1",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25
    )
    await profile_repo.create(
        user_id=user2.id,
        name="User2",
        description="Люблю спорт",
        gender=GenderEnum.female,
        age=23
    )
    
    mock_cache['action'].add_seen_user_id = AsyncMock()
    
    response = await client.post(
        "/actions",
        json={"to_user_id": user2.id, "action_type": "like"},
        headers={"X-Telegram-ID": "act_user1"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "action_id" in data
    assert data["success"] == True


@pytest.mark.asyncio
async def test_send_action_multiple_times(client, session, mock_cache):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user1 = await user_repo.create(telegram_id="act_multi1", username="@multi1")
    user2 = await user_repo.create(telegram_id="act_multi2", username="@multi2")
    
    await profile_repo.create(
        user_id=user1.id,
        name="User1",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25
    )
    await profile_repo.create(
        user_id=user2.id,
        name="User2",
        description="Люблю спорт",
        gender=GenderEnum.female,
        age=23
    )
    
    mock_cache['action'].add_seen_user_id = AsyncMock()
    
    response1 = await client.post(
        "/actions",
        json={"to_user_id": user2.id, "action_type": "like"},
        headers={"X-Telegram-ID": "act_multi1"}
    )
    assert response1.status_code == 200
    action_id_1 = response1.json()["action_id"]
    
    response2 = await client.post(
        "/actions",
        json={"to_user_id": user2.id, "action_type": "like"},
        headers={"X-Telegram-ID": "act_multi1"}
    )
    assert response2.status_code == 200
    action_id_2 = response2.json()["action_id"]
    
    assert action_id_2 != action_id_1


@pytest.mark.asyncio
async def test_send_action_self_raises(client, session):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user = await user_repo.create(telegram_id="act_self", username="@self")
    await profile_repo.create(
        user_id=user.id,
        name="Self",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25
    )
    
    response = await client.post(
        "/actions",
        json={"to_user_id": user.id, "action_type": "like"},
        headers={"X-Telegram-ID": "act_self"}
    )
    
    assert response.status_code == 400
