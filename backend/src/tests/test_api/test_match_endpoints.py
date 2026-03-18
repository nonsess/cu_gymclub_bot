import pytest
from unittest.mock import AsyncMock
from src.models.profile import GenderEnum
from src.models.action import ActionTypeEnum


@pytest.mark.asyncio
async def test_get_incoming_like_success(client, session):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    from src.repositories.action import ActionRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    action_repo = ActionRepository(session)
    
    receiver = await user_repo.create(telegram_id="111222333", username="@receiver")
    await profile_repo.create(
        user_id=receiver.id,
        name="Receiver",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.female,
        age=25
    )
    
    sender = await user_repo.create(telegram_id="444555666", username="@sender")
    await profile_repo.create(
        user_id=sender.id,
        name="Sender",
        description="Люблю спорт",
        gender=GenderEnum.male,
        age=30
    )
    
    await action_repo.create(
        from_user_id=sender.id,
        to_user_id=receiver.id,
        action_type=ActionTypeEnum.like.value.lower()
    )
    
    response = await client.get(
        "/matches/incoming/next",
        headers={"X-Telegram-ID": "111222333"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sender"
    assert data["user_id"] == sender.id


@pytest.mark.asyncio
async def test_get_incoming_like_no_more_likes(client, session):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user = await user_repo.create(telegram_id="777888999", username="@lonely")
    await profile_repo.create(
        user_id=user.id,
        name="Lonely",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25
    )
    
    response = await client.get(
        "/matches/incoming/next",
        headers={"X-Telegram-ID": "777888999"}
    )
    
    assert response.status_code in [404, 410]


@pytest.mark.asyncio
async def test_get_incoming_like_excludes_answered(client, session, mock_cache):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    from src.repositories.action import ActionRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    action_repo = ActionRepository(session)
    
    receiver = await user_repo.create(telegram_id="222333444", username="@chooser")
    await profile_repo.create(
        user_id=receiver.id,
        name="Chooser",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.female,
        age=25
    )
    
    sender1 = await user_repo.create(telegram_id="222333445", username="@sender1")
    await profile_repo.create(
        user_id=sender1.id,
        name="Sender1",
        description="Люблю спорт",
        gender=GenderEnum.male,
        age=30
    )
    
    sender2 = await user_repo.create(telegram_id="222333446", username="@sender2")
    await profile_repo.create(
        user_id=sender2.id,
        name="Sender2",
        description="Люблю кроссфит",
        gender=GenderEnum.male,
        age=28
    )
    
    action1 = await action_repo.create(
        from_user_id=sender1.id,
        to_user_id=receiver.id,
        action_type=ActionTypeEnum.like.value.lower()
    )
    action2 = await action_repo.create(
        from_user_id=sender2.id,
        to_user_id=receiver.id,
        action_type=ActionTypeEnum.like.value.lower()
    )
    
    await action_repo.mark_as_responded(action1.id)
    await session.commit()
    
    mock_cache['action'].add_seen_user_id = AsyncMock()
    
    response = await client.get(
        "/matches/incoming/next",
        headers={"X-Telegram-ID": "222333444"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sender2"
    assert data["incoming_action_id"] == action2.id


@pytest.mark.asyncio
async def test_decide_incoming_like_creates_match(client, session, mock_cache):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    from src.repositories.action import ActionRepository
    from src.repositories.base import BaseRepository
    from src.models.match import Match
    from src.models.action import ActionTypeEnum
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    action_repo = ActionRepository(session)
    
    user1 = await user_repo.create(telegram_id="333444555", username="@user1")
    await profile_repo.create(
        user_id=user1.id,
        name="User1",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25
    )
    
    user2 = await user_repo.create(telegram_id="333444556", username="@user2")
    await profile_repo.create(
        user_id=user2.id,
        name="User2",
        description="Люблю спорт",
        gender=GenderEnum.female,
        age=23
    )
    
    incoming = await action_repo.create(
        from_user_id=user1.id,
        to_user_id=user2.id,
        action_type=ActionTypeEnum.like.value.lower()
    )
    
    mock_cache['action'].add_seen_user_id = AsyncMock()
    
    response = await client.post(
        "/matches/incoming/decide",
        json={
            "action_id": incoming.id,
            "decision": "like"
        },
        headers={"X-Telegram-ID": "333444556"}
    )
    
    assert response.status_code in [200, 204]
    
    base_match_repo = BaseRepository(Match, session)
    matches = await base_match_repo.get_all(limit=10)
    match_found = any({m.user1_id, m.user2_id} == {user1.id, user2.id} for m in matches)
    assert match_found


@pytest.mark.asyncio
async def test_decide_incoming_dislike_no_match(client, session, mock_cache):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    from src.repositories.action import ActionRepository
    from src.repositories.base import BaseRepository
    from src.models.match import Match
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    action_repo = ActionRepository(session)
    
    user1 = await user_repo.create(telegram_id="444555666", username="@userA")
    await profile_repo.create(
        user_id=user1.id,
        name="UserA",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.female,
        age=25
    )
    
    user2 = await user_repo.create(telegram_id="444555667", username="@userB")
    await profile_repo.create(
        user_id=user2.id,
        name="UserB",
        description="Люблю спорт",
        gender=GenderEnum.male,
        age=30
    )
    
    incoming = await action_repo.create(
        from_user_id=user1.id,
        to_user_id=user2.id,
        action_type=ActionTypeEnum.like.value.lower()
    )
    
    mock_cache['action'].add_seen_user_id = AsyncMock()
    
    response = await client.post(
        "/matches/incoming/decide",
        json={
            "action_id": incoming.id,
            "decision": "dislike"
        },
        headers={"X-Telegram-ID": "444555667"}
    )
    
    assert response.status_code in [200, 204]
    
    base_match_repo = BaseRepository(Match, session)
    matches = await base_match_repo.get_all(limit=10)
    match_found = any({m.user1_id, m.user2_id} == {user1.id, user2.id} for m in matches)
    assert not match_found


@pytest.mark.asyncio
async def test_decide_incoming_self_action_error(client, session):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    user = await user_repo.create(telegram_id="555666777", username="@self")
    await profile_repo.create(
        user_id=user.id,
        name="Self",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25
    )
    
    response = await client.post(
        "/matches/incoming/decide",
        json={
            "action_id": 999999,
            "decision": "like"
        },
        headers={"X-Telegram-ID": "555666777"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_decide_incoming_profile_not_found(client, session):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)

    user = await user_repo.create(telegram_id="666777888", username="@viewer")
    await profile_repo.create(
        user_id=user.id,
        name="Self",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25
    )

    response = await client.post(
        "/matches/incoming/999999/decide",
        json={
            "to_user_id": "999999",
            "action_type": "like"
        },
        headers={"X-Telegram-ID": "666777888"}
    )
    
    assert response.status_code == 404
