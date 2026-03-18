import pytest
from src.repositories.action import ActionRepository
from src.repositories.user import UserRepository
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
async def test_get_next_incoming_like_returns_one(session):
    from src.repositories.user import UserRepository
    from src.repositories.profile import ProfileRepository
    from src.repositories.action import ActionRepository
    from src.models.profile import GenderEnum
    
    user_repo = UserRepository(session)
    profile_repo = ProfileRepository(session)
    action_repo = ActionRepository(session)
    
    receiver = await user_repo.create(telegram_id="recv_one")
    sender1 = await user_repo.create(telegram_id="send1_one")
    sender2 = await user_repo.create(telegram_id="send2_one")
    
    await profile_repo.create(
        user_id=receiver.id,
        name="Receiver",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.female,
        age=25
    )
    await profile_repo.create(
        user_id=sender1.id,
        name="Sender1",
        description="Люблю спорт",
        gender=GenderEnum.male,
        age=30
    )
    await profile_repo.create(
        user_id=sender2.id,
        name="Sender2",
        description="Люблю кроссфит",
        gender=GenderEnum.male,
        age=28
    )
    
    await action_repo.create(
        from_user_id=sender1.id,
        to_user_id=receiver.id,
        action_type="like"
    )
    await action_repo.create(
        from_user_id=sender2.id,
        to_user_id=receiver.id,
        action_type="like"
    )
    
    action = await action_repo.get_next_incoming_like(receiver.id)
    
    assert action is not None
    assert action.from_user_id in [sender1.id, sender2.id]
