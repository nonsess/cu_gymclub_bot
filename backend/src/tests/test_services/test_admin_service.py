import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.admin import AdminService
from src.core.exceptions.admin import InvalidPermissions
from src.core.exceptions.user import UserNotFound


@pytest.fixture
def mock_repos():
    with patch('src.services.admin.UserRepository') as MockUserRepo, \
         patch('src.services.admin.ProfileRepository') as MockProfileRepo, \
         patch('src.services.admin.AdminRepository') as MockAdminRepo, \
         patch('src.services.admin.cache') as MockCache, \
         patch('src.services.admin.telegram_service') as MockTelegram:
        
        mock_user_repo = MockUserRepo.return_value
        mock_profile_repo = MockProfileRepo.return_value
        mock_admin_repo = MockAdminRepo.return_value
        mock_cache = MockCache
        mock_telegram = MockTelegram
        
        mock_user_repo.get = AsyncMock()
        mock_user_repo.update = AsyncMock()
        mock_user_repo.get_active_telegram_ids = AsyncMock(return_value=[])
        mock_profile_repo.get_by_user_id = AsyncMock()
        mock_profile_repo.delete = AsyncMock()
        mock_admin_repo.export_profiles_to_csv = AsyncMock(return_value="csv_data")
        
        mock_cache.invalidate_profile = AsyncMock()
        
        mock_telegram.send_message = AsyncMock(return_value=True)
        
        yield {
            'user': mock_user_repo,
            'profile': mock_profile_repo,
            'admin': mock_admin_repo,
            'cache': mock_cache,
            'telegram': mock_telegram,
        }


@pytest.fixture
def admin_service(session, mock_repos):
    return AdminService(session)


@pytest.fixture
def mock_admin_user():
    user = MagicMock()
    user.id = 999
    user.telegram_id = "121231231"
    user.chat_id = "121231231"
    user.username = "admin"
    user.first_name = "Admin"
    return user


@pytest.fixture
def mock_regular_user():
    user = MagicMock()
    user.id = 1
    user.telegram_id = "999888777"
    user.username = "user"
    user.first_name = "User"
    return user


@pytest.mark.asyncio
async def test_ensure_permissions_admin_ok(admin_service, mock_admin_user):
    await admin_service._ensure_permissions(mock_admin_user)


@pytest.mark.asyncio
async def test_ensure_permissions_regular_user_raises(admin_service, mock_regular_user):
    with pytest.raises(InvalidPermissions):
        await admin_service._ensure_permissions(mock_regular_user)


@pytest.mark.asyncio
async def test_ban_user_success(admin_service, mock_repos, mock_admin_user):
    mock_target = MagicMock(
        id=42,
        telegram_id="banned_user",
        username="banned",
        first_name="Banned"
    )
    mock_repos['user'].get = AsyncMock(return_value=mock_target)
    mock_repos['user'].update = AsyncMock()
    
    mock_profile = MagicMock(id=100)
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_profile)
    mock_repos['profile'].delete = AsyncMock()
    
    await admin_service.ban_user(user_id=42, admin=mock_admin_user)
    
    mock_repos['user'].update.assert_called_once_with(mock_target, is_banned=True)
    mock_repos['profile'].delete.assert_called_once_with(mock_profile)
    mock_repos['cache'].invalidate_profile.assert_called_once_with(100)


@pytest.mark.asyncio
async def test_ban_user_not_found_raises(admin_service, mock_repos, mock_admin_user):
    mock_repos['user'].get = AsyncMock(return_value=None)
    
    with pytest.raises(UserNotFound):
        await admin_service.ban_user(user_id=999, admin=mock_admin_user)


@pytest.mark.asyncio
async def test_ban_user_cannot_ban_self(admin_service, mock_repos, mock_admin_user):
    mock_repos['user'].get = AsyncMock(return_value=mock_admin_user)
    
    with pytest.raises(InvalidPermissions):
        await admin_service.ban_user(user_id=mock_admin_user.id, admin=mock_admin_user)


@pytest.mark.asyncio
async def test_export_profiles_to_csv(admin_service, mock_repos, mock_admin_user):
    mock_csv = "profile_id,user_id,name\n1,2,Test"
    mock_repos['admin'].export_profiles_to_csv = AsyncMock(return_value=mock_csv)
    
    result = await admin_service.export_profiles_to_csv(
        admin=mock_admin_user,
        limit=100,
        offset=0,
        is_active=True
    )
    
    assert result == mock_csv
    
    mock_repos['admin'].export_profiles_to_csv.assert_called_once_with(
        100, 0, True
    )


@pytest.mark.asyncio
async def test_run_broadcast_task_basic(admin_service, mock_repos, mock_admin_user):
    with patch('src.services.admin.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        mock_sleep.return_value = None
        
        mock_repos['user'].get_active_telegram_ids = AsyncMock(
            side_effect=[
                [("111",), ("222",)],
                []
            ]
        )
        
        import asyncio
        try:
            await asyncio.wait_for(
                admin_service.run_broadcast_task(
                    admin=mock_admin_user,
                    admin_chat_id=121231231,
                    message_text="Тестовая рассылка",
                    batch_size=2,
                    delay_between=0.01
                ),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            pytest.fail("Broadcast task timed out")
        
    user_messages = [
        call_args for call_args in mock_repos['telegram'].send_message.call_args_list
        if call_args[1]['chat_id'] in ['111', '222']
    ]
    assert len(user_messages) == 2


@pytest.mark.asyncio
async def test_send_broadcast_stats_to_admin(admin_service, mock_repos, mock_admin_user):
    await admin_service._send_broadcast_stats_to_admin(
        admin_chat_id=121231231,
        task_id="abc123",
        stats={"total": 10, "sent": 8, "failed": 1, "blocked": 1},
        message_preview="Привет!"
    )
    
    mock_repos['telegram'].send_message.assert_called_once()
    call_args = mock_repos['telegram'].send_message.call_args
    
    assert call_args[1]['chat_id'] == 121231231
    assert "Рассылка завершена" in call_args[1]['text']
    assert "80.0%" in call_args[1]['text']
    assert "abc123" in call_args[1]['text']