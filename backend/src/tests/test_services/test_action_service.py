import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.action import ActionService
from src.models.action import ActionTypeEnum
from src.core.exceptions.action import SelfActionException


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
        
        mock_user_repo.get = AsyncMock(return_value=MagicMock(
            id=1,
            telegram_id="123456789",
            username="@testuser",
            first_name="Test"
        ))
        mock_action_repo.create = AsyncMock()
        mock_action_repo.check_mutual_like = AsyncMock(return_value=False)
        mock_match_repo.create_match = AsyncMock(return_value=MagicMock(id=999))
        mock_profile_repo.get_by_user_id = AsyncMock(return_value=MagicMock(
            id=1,
            name="Test",
            description="Desc",
            gender="male",
            age=25,
            media=[],
            is_active=True
        ))
        
        mock_cache.add_seen_user_id = AsyncMock()
        mock_cache.get_seen_user_ids = AsyncMock(return_value=[])
        
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
async def test_send_action_self_action_raises(action_service):
    with pytest.raises(SelfActionException):
        await action_service.send_action(
            from_user_id=1,
            to_user_id=1,
            action_type=ActionTypeEnum.like
        )


@pytest.mark.asyncio
async def test_send_like_creates_action(action_service, mock_repos):
    mock_repos['action'].create = AsyncMock()
    mock_repos['action'].check_mutual_like = AsyncMock(return_value=False)
    
    await action_service.send_action(
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.like
    )
    
    mock_repos['action'].create.assert_called_once_with(
        from_user_id=1,
        to_user_id=2,
        action_type='like',
        report_reason=None
    )
    
    assert mock_repos['cache'].add_seen_user_id.call_count == 2


@pytest.mark.asyncio
async def test_send_like_creates_match_when_mutual(action_service, mock_repos):
    mock_repos['action'].create = AsyncMock()
    mock_repos['action'].check_mutual_like = AsyncMock(return_value=True)
    mock_repos['match'].create_match = AsyncMock(return_value=MagicMock(id=999))
    
    await action_service.send_action(
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.like
    )
    
    mock_repos['match'].create_match.assert_called_once_with(1, 2)
    
    assert mock_repos['telegram'].notify_new_match.call_count == 2

@pytest.mark.asyncio
async def test_send_like_without_match_sends_notification(action_service, mock_repos):
    mock_repos['action'].create = AsyncMock()
    mock_repos['action'].check_mutual_like = AsyncMock(return_value=False)
    
    mock_from_user = MagicMock(
        id=1,
        telegram_id="111111",
        username="@sender",
        first_name="Sender"
    )
    mock_to_user = MagicMock(
        id=2,
        telegram_id="987654321",
        username="@recipient",
        first_name="Recipient"
    )

    mock_repos['user'].get = AsyncMock(side_effect=[mock_to_user, mock_from_user])
    
    await action_service.send_action(
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.like
    )
        
    mock_repos['telegram'].notify_new_like.assert_called_once_with(
        chat_id="987654321"
    )

@pytest.mark.asyncio
async def test_send_report_with_reason(action_service, mock_repos):
    mock_repos['action'].create = AsyncMock()

    await action_service.send_action(
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.report,
        report_reason="Спам"
    )
    
    mock_repos['action'].create.assert_called_once_with(
        from_user_id=1,
        to_user_id=2,
        action_type='report',
        report_reason="Спам"
    )


@pytest.mark.asyncio
async def test_send_report_notifies_admin(action_service, mock_repos):
    mock_repos['action'].create = AsyncMock()
    
    mock_profile = MagicMock(
        id=2,
        name="Reported User",
        description="Люблю тренироваться каждый день в зале",
        gender="male",
        age=25,
        media=[MagicMock(type="photo", file_id="abc123")],
        is_active=True
    )
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_profile)
    
    mock_reporter = MagicMock(
        id=1,
        username="reporter",
        telegram_id="111111"
    )
    mock_reported = MagicMock(
        id=2,
        username="reported",
        telegram_id="222222"
    )

    mock_repos['user'].get = AsyncMock(side_effect=[mock_reported, mock_reporter])
    
    await action_service.send_action(
        from_user_id=1,
        to_user_id=2,
        action_type=ActionTypeEnum.report,
        report_reason="Фейк"
    )
    
    mock_repos['telegram'].send_media_group.assert_called_once()
    
    call_args = mock_repos['telegram'].send_media_group.call_args
    assert call_args[1]['chat_id'] == "121231231"


@pytest.mark.asyncio
async def test_decide_on_incoming_creates_action(action_service, mock_repos):
    mock_repos['action'].create = AsyncMock()
    
    await action_service.decide_on_incoming(
        viewer_user_id=2,
        target_user_id=1,
        action_type=ActionTypeEnum.like
    )
    
    mock_repos['action'].create.assert_called_once_with(
        from_user_id=2,
        to_user_id=1,
        action_type=ActionTypeEnum.like
    )


@pytest.mark.asyncio
async def test_decide_on_incoming_like_creates_match(action_service, mock_repos):
    mock_repos['action'].create = AsyncMock()
    mock_repos['match'].create_match = AsyncMock(return_value=MagicMock(id=999))
    
    await action_service.decide_on_incoming(
        viewer_user_id=2,
        target_user_id=1,
        action_type=ActionTypeEnum.like
    )
    
    mock_repos['match'].create_match.assert_called_once_with(2, 1)
    assert mock_repos['telegram'].notify_new_match.call_count == 2


@pytest.mark.asyncio
async def test_decide_on_incoming_dislike_no_match(action_service, mock_repos):
    mock_repos['action'].create = AsyncMock()
    mock_repos['match'].create_match = AsyncMock()
    
    await action_service.decide_on_incoming(
        viewer_user_id=2,
        target_user_id=1,
        action_type=ActionTypeEnum.dislike
    )
    
    mock_repos['match'].create_match.assert_not_called()
    mock_repos['telegram'].notify_new_match.assert_not_called()