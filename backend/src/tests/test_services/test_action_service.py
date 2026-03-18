import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.action import ActionService
from src.models.action import ActionTypeEnum
from src.core.exceptions.action import (
    SelfActionException,
    ActionAlreadyRespondedException
)
from src.core.exceptions.profile import ProfileNotFoundException


@pytest.fixture
def mock_repos():
    with patch('src.services.action.UserRepository') as MockUserRepo, \
         patch('src.services.action.ActionRepository') as MockActionRepo, \
         patch('src.services.action.MatchRepository') as MockMatchRepo, \
         patch('src.services.action.ProfileRepository') as MockProfileRepo, \
         patch('src.services.action.cache') as MockCache, \
         patch('src.services.action.telegram_service') as MockTelegram:
        
        mock_user_repo = MockUserRepo.return_value
        mock_action_repo = MockActionRepo.return_value
        mock_match_repo = MockMatchRepo.return_value
        mock_profile_repo = MockProfileRepo.return_value
        mock_cache = MockCache
        mock_telegram = MockTelegram
        
        mock_user_repo.get = AsyncMock(return_value=MagicMock(id=1, telegram_id="123", username="@test", first_name="Test"))
        mock_action_repo.create = AsyncMock(return_value=MagicMock(id=999, is_responded=False))
        mock_action_repo.get = AsyncMock()
        mock_action_repo.mark_as_responded = AsyncMock()
        mock_match_repo.create_match = AsyncMock(return_value=MagicMock(id=100))
        mock_profile_repo.get_by_user_id = AsyncMock()
        
        mock_cache.add_seen_user_id = AsyncMock()
        
        mock_telegram.send_message = AsyncMock(return_value=True)
        mock_telegram.notify_new_like = AsyncMock()
        mock_telegram.notify_new_match = AsyncMock()
        mock_telegram.send_media_group = AsyncMock()
        
        yield {
            'user': mock_user_repo,
            'action': mock_action_repo,
            'match': mock_match_repo,
            'profile': mock_profile_repo,
            'cache': mock_cache,
            'telegram': mock_telegram,
        }


@pytest.fixture
def action_service(session, mock_repos):
    return ActionService(session)


@pytest.mark.asyncio
async def test_send_action_returns_action_id(action_service, mock_repos):
    mock_action = MagicMock(id=999)
    mock_repos['action'].create = AsyncMock(return_value=mock_action)
    
    result = await action_service.send_action(
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.like
    )
    
    assert result == 999


@pytest.mark.asyncio
async def test_send_action_self_raises(action_service):
    with pytest.raises(SelfActionException):
        await action_service.send_action(1, 1, ActionTypeEnum.like)


@pytest.mark.asyncio
async def test_send_like_sends_notification(action_service, mock_repos):
    mock_action = MagicMock(id=999)
    mock_repos['action'].create = AsyncMock(return_value=mock_action)
    
    with patch('src.services.action.telegram_service') as mock_telegram:
        mock_telegram.notify_new_like = AsyncMock()
        
        await action_service.send_action(1, 2, ActionTypeEnum.like)
        
        mock_telegram.notify_new_like.assert_called_once()


@pytest.mark.asyncio
async def test_send_report_with_reason_sends_to_admin(action_service, mock_repos):
    mock_action = MagicMock(id=999)
    mock_repos['action'].create = AsyncMock(return_value=mock_action)
    
    mock_profile = MagicMock(
        name="Test",
        description="Люблю тренироваться каждый день в зале",
        gender="male",
        age=25,
        media=[]
    )
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_profile)
    
    mock_user = MagicMock(username="testuser", telegram_id="123")
    mock_repos['user'].get = AsyncMock(return_value=mock_user)
    
    with patch('src.services.action.telegram_service') as mock_telegram:
        mock_telegram.send_message = AsyncMock(return_value=True)
        
        await action_service.send_action(
            from_user_id=1,
            to_user_id=2,
            action_type=ActionTypeEnum.report,
            report_reason="Спам"
        )
        
        mock_telegram.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_decide_on_incoming_valid_action_creates_response(action_service, mock_repos):
    incoming = MagicMock(
        id=123,
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.like,
        is_responded=False
    )
    mock_repos['action'].get = AsyncMock(return_value=incoming)
    mock_repos['action'].mark_as_responded = AsyncMock()
    mock_repos['action'].create = AsyncMock(return_value=MagicMock(id=999))
    
    mock_profile = MagicMock(id=1, is_active=True)
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_profile)
    
    result = await action_service.decide_on_incoming(
        viewer_user_id=2,
        action_id=123,
        decision_type=ActionTypeEnum.like,
        report_reason=None
    )
    
    assert result['success'] == True
    mock_repos['action'].mark_as_responded.assert_called_once_with(123)
    mock_repos['action'].create.assert_called_once()


@pytest.mark.asyncio
async def test_decide_on_incoming_like_creates_match(action_service, mock_repos):
    incoming = MagicMock(
        id=123,
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.like,
        is_responded=False
    )
    mock_repos['action'].get = AsyncMock(return_value=incoming)
    mock_repos['action'].mark_as_responded = AsyncMock()
    mock_repos['action'].create = AsyncMock(return_value=MagicMock(id=999))
    
    mock_profile = MagicMock(id=1, is_active=True)
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_profile)
    
    with patch('src.services.action.telegram_service') as mock_telegram:
        mock_telegram.notify_new_match = AsyncMock()
        
        result = await action_service.decide_on_incoming(
            viewer_user_id=2,
            action_id=123,
            decision_type=ActionTypeEnum.like,
            report_reason=None
        )
        
        assert 'match_id' in result
        mock_repos['match'].create_match.assert_called_once_with(2, 1)
        assert mock_telegram.notify_new_match.call_count == 2


@pytest.mark.asyncio
async def test_decide_on_incoming_action_not_found_raises(action_service, mock_repos):
    mock_repos['action'].get = AsyncMock(return_value=None)
    
    with pytest.raises(ProfileNotFoundException):
        await action_service.decide_on_incoming(
            viewer_user_id=2,
            action_id=999,
            decision_type=ActionTypeEnum.like,
            report_reason=None
        )


@pytest.mark.asyncio
async def test_decide_on_incoming_wrong_recipient_raises(action_service, mock_repos):
    incoming = MagicMock(
        id=123,
        from_user_id=1,
        to_user_id=3,
        action_type=ActionTypeEnum.like,
        is_responded=False
    )
    mock_repos['action'].get = AsyncMock(return_value=incoming)
    
    with pytest.raises(ProfileNotFoundException):
        await action_service.decide_on_incoming(
            viewer_user_id=2,
            action_id=123,
            decision_type=ActionTypeEnum.like,
            report_reason=None
        )


@pytest.mark.asyncio
async def test_decide_on_incoming_not_like_raises(action_service, mock_repos):
    incoming = MagicMock(
        id=123,
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.dislike,
        is_responded=False
    )
    mock_repos['action'].get = AsyncMock(return_value=incoming)
    
    with pytest.raises(Exception):
        await action_service.decide_on_incoming(
            viewer_user_id=2,
            action_id=123,
            decision_type=ActionTypeEnum.like,
            report_reason=None
        )


@pytest.mark.asyncio
async def test_decide_on_incoming_already_responded_raises(action_service, mock_repos):
    incoming = MagicMock(
        id=123,
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.like,
        is_responded=True
    )
    mock_repos['action'].get = AsyncMock(return_value=incoming)
    
    with pytest.raises(ActionAlreadyRespondedException):
        await action_service.decide_on_incoming(
            viewer_user_id=2,
            action_id=123,
            decision_type=ActionTypeEnum.like,
            report_reason=None
        )


@pytest.mark.asyncio
async def test_get_next_incoming_like_returns_profile_and_action_id(action_service, mock_repos):
    from src.models.action import UserAction, ActionTypeEnum
    
    incoming = MagicMock(
        spec=UserAction,
        id=123,
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.like.value.lower(),
        is_responded=False
    )
    
    mock_repos['action'].get_next_incoming_like = AsyncMock(return_value=incoming)
    
    mock_profile = MagicMock(id=1, is_active=True)
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_profile)
    
    result = await action_service.get_next_incoming_like(user_id=2)
    
    assert result['profile'] == mock_profile
    assert result['action_id'] == 123
    mock_repos['action'].get_next_incoming_like.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_get_next_incoming_like_no_incoming_raises(action_service, mock_repos):
    from src.core.exceptions.profile import NoMoreProfilesException
    
    mock_repos['action'].get_next_incoming_like = AsyncMock(return_value=None)
    
    with pytest.raises(NoMoreProfilesException):
        await action_service.get_next_incoming_like(user_id=2)
    
    mock_repos['action'].get_next_incoming_like.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_multiple_likes_same_users_proper_handling(action_service, mock_repos):
    from src.models.action import ActionTypeEnum
    
    action_1 = MagicMock(id=100, is_responded=False)
    action_2 = MagicMock(id=101, is_responded=False)
    action_3 = MagicMock(id=102, is_responded=False)
    
    mock_repos['action'].create = AsyncMock(side_effect=[action_1, action_2, action_3])
    mock_repos['action'].check_mutual_like = AsyncMock(return_value=False)
    mock_repos['action'].get_incoming_likes = AsyncMock(return_value=[action_2])
    mock_repos['action'].get = AsyncMock(return_value=action_2)
    mock_repos['action'].mark_as_responded = AsyncMock()
    
    mock_profile = MagicMock(id=1, is_active=True)
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_profile)
    
    with patch('src.services.action.telegram_service') as mock_telegram:
        mock_telegram.notify_new_like = AsyncMock()
        
        result_1 = await action_service.send_action(
            from_user_id=1,
            to_user_id=2,
            action_type=ActionTypeEnum.like
        )
        assert result_1 == 100
        
        result_2 = await action_service.send_action(
            from_user_id=1,
            to_user_id=2,
            action_type=ActionTypeEnum.like
        )
        assert result_2 == 101
        assert result_2 != result_1
        
        result_3 = await action_service.send_action(
            from_user_id=1,
            to_user_id=2,
            action_type=ActionTypeEnum.like
        )
        assert result_3 == 102
        
        assert mock_repos['action'].create.call_count == 3
