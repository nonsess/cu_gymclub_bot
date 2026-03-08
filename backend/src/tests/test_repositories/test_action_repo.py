import pytest
from src.models.profile import GenderEnum
from src.repositories.action import ActionRepository
from src.repositories.user import UserRepository
from src.repositories.profile import ProfileRepository
from src.models.action import ActionTypeEnum


@pytest.mark.asyncio
async def test_create_action(session):
    user_repo = UserRepository(session)
    from_user = await user_repo.create(telegram_id="800001")
    to_user = await user_repo.create(telegram_id="800002")
    
    repo = ActionRepository(session)
    action = await repo.create(
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        action_type=ActionTypeEnum.like
    )
    
    assert action.from_user_id == from_user.id
    assert action.to_user_id == to_user.id
    assert action.action_type == ActionTypeEnum.like


@pytest.mark.asyncio
async def test_create_action_with_report_reason(session):
    user_repo = UserRepository(session)
    from_user = await user_repo.create(telegram_id="800003")
    to_user = await user_repo.create(telegram_id="800004")
    
    repo = ActionRepository(session)
    action = await repo.create(
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        action_type=ActionTypeEnum.report,
        report_reason="Спам"
    )
    
    assert action.action_type == ActionTypeEnum.report
    assert action.report_reason == "Спам"


@pytest.mark.asyncio
async def test_get_action(session):
    user_repo = UserRepository(session)
    from_user = await user_repo.create(telegram_id="800005")
    to_user = await user_repo.create(telegram_id="800006")
    
    repo = ActionRepository(session)
    await repo.create(
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        action_type=ActionTypeEnum.like
    )
    
    action = await repo.get_action(from_user.id, to_user.id)
    
    assert action is not None
    assert action.action_type == ActionTypeEnum.like


@pytest.mark.asyncio
async def test_get_action_not_found(session):
    repo = ActionRepository(session)
    action = await repo.get_action(999, 999)
    assert action is None


@pytest.mark.asyncio
async def test_check_mutual_like_true(session):
    user_repo = UserRepository(session)
    user1 = await user_repo.create(telegram_id="800007")
    user2 = await user_repo.create(telegram_id="800008")
    
    repo = ActionRepository(session)
    await repo.create(
        from_user_id=user1.id,
        to_user_id=user2.id,
        action_type=ActionTypeEnum.like
    )
    await repo.create(
        from_user_id=user2.id,
        to_user_id=user1.id,
        action_type=ActionTypeEnum.like
    )
    
    is_match = await repo.check_mutual_like(user1.id, user2.id)
    assert is_match == True


@pytest.mark.asyncio
async def test_check_mutual_like_false(session):
    user_repo = UserRepository(session)
    user1 = await user_repo.create(telegram_id="800009")
    user2 = await user_repo.create(telegram_id="800010")
    
    repo = ActionRepository(session)
    await repo.create(
        from_user_id=user1.id,
        to_user_id=user2.id,
        action_type=ActionTypeEnum.like
    )
    
    is_match = await repo.check_mutual_like(user1.id, user2.id)
    assert is_match == False


@pytest.mark.asyncio
async def test_get_incoming_likes(session):
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    receiver = await user_repo.create(telegram_id="800011")
    await profile_repo.create(
        user_id=receiver.id,
        name="Receiver",
        description="Desc",
        gender=GenderEnum.female
    )
    
    sender1 = await user_repo.create(telegram_id="800012")
    sender2 = await user_repo.create(telegram_id="800013")
    
    repo = ActionRepository(session)
    await repo.create(
        from_user_id=sender1.id,
        to_user_id=receiver.id,
        action_type=ActionTypeEnum.like
    )
    await repo.create(
        from_user_id=sender2.id,
        to_user_id=receiver.id,
        action_type=ActionTypeEnum.like
    )

    incoming = await repo.get_incoming_likes(receiver.id)
    
    assert len(incoming) == 2
    assert all(a.action_type == ActionTypeEnum.like for a in incoming)


@pytest.mark.asyncio
async def test_get_incoming_likes_excludes_answered(session):
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    
    receiver = await user_repo.create(telegram_id="800014")
    await profile_repo.create(
        user_id=receiver.id,
        name="Receiver",
        description="Desc",
        gender=GenderEnum.female
    )
    
    sender = await user_repo.create(telegram_id="800015")
    
    repo = ActionRepository(session)

    await repo.create(from_user_id=sender.id, to_user_id=receiver.id, action_type=ActionTypeEnum.like)
    await repo.create(from_user_id=receiver.id, to_user_id=sender.id, action_type=ActionTypeEnum.dislike)
    
    incoming = await repo.get_incoming_likes(receiver.id)
    
    assert len(incoming) == 0