import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.profile import ProfileService
from src.schemas.profile import ProfileCreate, ProfileUpdate
from src.models.profile import GenderEnum
from src.core.exceptions.profile import (
    ProfileNotFoundException,
    NoMoreProfilesException,
    ProfileAlreadyExistsException
)


@pytest.fixture
def mock_repos():
    with patch('src.services.profile.ProfileRepository') as MockProfileRepo:
        mock_profile_repo = MockProfileRepo.return_value
        
        mock_profile_repo.create = AsyncMock()
        mock_profile_repo.get_by_user_id = AsyncMock()
        mock_profile_repo.get = AsyncMock()
        mock_profile_repo.update = AsyncMock()
        mock_profile_repo.get_similar_profiles = AsyncMock(return_value=[])
        mock_profile_repo.get_random_profiles = AsyncMock(return_value=[])
        
        yield {'profile': mock_profile_repo}


@pytest.fixture
def profile_service(session, mock_repos):
    return ProfileService(session)


@pytest.mark.asyncio
async def test_get_profile_success(profile_service, mock_repos):
    mock_profile = MagicMock(
        id=1,
        user_id=1,
        name="Алексей",
        description="Люблю спорт каждый день",
        gender=GenderEnum.male,
        age=25,
        media=[],
        is_active=True,
        created_at="2024-01-01",
        updated_at="2024-01-01"
    )
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_profile)
    
    result = await profile_service.get_profile(user_id=1)
    
    assert result == mock_profile
    mock_repos['profile'].get_by_user_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_profile_not_found(profile_service, mock_repos):
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=None)
    
    with pytest.raises(ProfileNotFoundException):
        await profile_service.get_profile(user_id=999)


@pytest.mark.asyncio
async def test_create_profile_success(profile_service, mock_repos):
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=None)
    
    with patch('src.services.profile.embedding_service') as mock_embedding:
        mock_embedding.generate_embedding = AsyncMock(return_value=[0.1] * 384)
        
        mock_created = MagicMock(id=1, user_id=1, name="Алексей")
        mock_repos['profile'].create = AsyncMock(return_value=mock_created)
        
        profile_data = ProfileCreate(
            name="Алексей",
            description="Люблю тренироваться каждый день в зале",
            gender=GenderEnum.male,
            age=25,
            media=[]
        )
        
        result = await profile_service.create_profile(user_id=1, profile_data=profile_data)
        
        assert result == mock_created
        mock_repos['profile'].create.assert_called_once()


@pytest.mark.asyncio
async def test_create_profile_already_exists(profile_service, mock_repos):
    mock_existing = MagicMock(id=1)
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_existing)
    
    profile_data = ProfileCreate(
        name="Алексей",
        description="Люблю тренироваться каждый день в зале",
        gender=GenderEnum.male,
        age=25,
        media=[]
    )
    
    with pytest.raises(ProfileAlreadyExistsException):
        await profile_service.create_profile(user_id=1, profile_data=profile_data)


@pytest.mark.asyncio
async def test_update_profile_success(profile_service, mock_repos):
    mock_profile = MagicMock(
        id=1,
        user_id=1,
        name="Old",
        description="Old desc",
        gender=GenderEnum.male,
        age=25,
        media=[],
        is_active=True
    )
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_profile)
    mock_repos['profile'].update = AsyncMock(return_value=mock_profile)
    
    with patch('src.services.profile.cache') as mock_cache:
        mock_cache.invalidate_profile = AsyncMock()
        
        update_data = ProfileUpdate(description="Новое описание профиля", age=30)
        
        result = await profile_service.update_profile(user_id=1, profile_data=update_data)
        
        assert result == mock_profile
        mock_cache.invalidate_profile.assert_called_once_with(1)
        mock_repos['profile'].update.assert_called_once()


@pytest.mark.asyncio
async def test_update_profile_not_found(profile_service, mock_repos):
    mock_repos['profile'].get_by_user_id = AsyncMock(return_value=None)
    
    update_data = ProfileUpdate(description="Новое описание профиля")
    
    with pytest.raises(ProfileNotFoundException):
        await profile_service.update_profile(user_id=999, profile_data=update_data)


@pytest.mark.asyncio
async def test_get_next_profile_from_cache(profile_service, mock_repos):
    with patch('src.services.profile.cache') as mock_cache:
        mock_cache.pop_from_queue = AsyncMock(return_value=42)
        mock_cache.get_cached_profile = AsyncMock(return_value={
            'id': 42,
            'user_id': 2,
            'name': 'Cached User',
            'description': 'Desc',
            'gender': 'male',
            'age': 25,
            'media': [],
            'is_active': True,
            'created_at': '2024-01-01',
            'updated_at': '2024-01-01'
        })
        mock_cache.add_seen_user_id = AsyncMock()
        
        result = await profile_service.get_next_profile(user_id=1)
        
        assert result['name'] == 'Cached User'
        mock_cache.add_seen_user_id.assert_called_once_with(1, 2)


@pytest.mark.asyncio
async def test_get_next_profile_from_db_when_cache_miss(profile_service, mock_repos):
    with patch('src.services.profile.cache') as mock_cache:
        mock_cache.pop_from_queue = AsyncMock(return_value=42)
        mock_cache.get_cached_profile = AsyncMock(return_value=None)
        
        mock_profile = MagicMock(
            spec=['id', 'user_id', 'name', 'description', 'gender', 'age', 'media', 'is_active', 'created_at', 'updated_at'],
            id=42,
            user_id=2,
            description='Desc',
            gender=GenderEnum.female,
            age=23,
            media=[],
            is_active=True,
            created_at='2024-01-01',
            updated_at='2024-01-02'
        )
        mock_profile.name = 'DB User'

        mock_repos['profile'].get = AsyncMock(return_value=mock_profile)
        mock_cache.cache_profile = AsyncMock()
        mock_cache.add_seen_user_id = AsyncMock()
        
        result = await profile_service.get_next_profile(user_id=1)
        
        assert result['name'] == 'DB User'
        mock_cache.cache_profile.assert_called_once()
    

@pytest.mark.asyncio
async def test_get_next_profile_fetches_similar_batch(profile_service, mock_repos):
    with patch('src.services.profile.cache') as mock_cache:
        mock_cache.pop_from_queue = AsyncMock(return_value=None)
        mock_cache.get_seen_user_ids = AsyncMock(return_value=[])
        mock_cache.fill_queue = AsyncMock()
        mock_cache.cache_profile = AsyncMock()
        
        mock_current = MagicMock(
            spec=['id', 'user_id', 'embedding'],
            id=1,
            user_id=1,
            embedding=[0.1] * 384
        )
        mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_current)
        
        mock_similar = MagicMock(
            spec=['id', 'user_id', 'name', 'description', 'gender', 'age', 'media', 'is_active', 'created_at', 'updated_at'],
            id=42,
            user_id=2,
            description='Desc',
            gender=GenderEnum.female,
            age=23,
            media=[],
            is_active=True,
            created_at='2024-01-01',
            updated_at='2024-01-02'
        )
        mock_similar.name = 'Similar User'

        mock_repos['profile'].get_similar_profiles = AsyncMock(return_value=[mock_similar])
        
        result = await profile_service.get_next_profile(user_id=1)
        
        assert result.name == 'Similar User'
        mock_cache.fill_queue.assert_called_once()


@pytest.mark.asyncio
async def test_get_next_profile_fallback_to_random(profile_service, mock_repos):
    with patch('src.services.profile.cache') as mock_cache:
        mock_cache.pop_from_queue = AsyncMock(return_value=None)
        mock_cache.get_seen_user_ids = AsyncMock(return_value=[])
        mock_cache.fill_queue = AsyncMock()
        mock_cache.cache_profile = AsyncMock()
        
        mock_current = MagicMock(
            spec=['id', 'user_id', 'embedding'],
            id=1,
            user_id=1,
            embedding=None
        )
        mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_current)
        
        mock_repos['profile'].get_similar_profiles = AsyncMock(return_value=[])
        
        mock_random = MagicMock(
            spec=['id', 'user_id', 'name', 'description', 'gender', 'age', 'media', 'is_active', 'created_at', 'updated_at'],
            id=99,
            user_id=3,
            description='Desc',
            gender=GenderEnum.male,
            age=28,
            media=['photo1'],
            is_active=True,
            created_at='2024-01-01',
            updated_at='2024-01-02'
        )
        mock_random.name = 'Random User'

        mock_repos['profile'].get_random_profiles = AsyncMock(return_value=[mock_random])
        
        result = await profile_service.get_next_profile(user_id=1)
        
        assert result.name == 'Random User'
        mock_repos['profile'].get_random_profiles.assert_called_once()


@pytest.mark.asyncio
async def test_get_next_profile_no_more_profiles(profile_service, mock_repos):
    with patch('src.services.profile.cache') as mock_cache:
        mock_cache.pop_from_queue = AsyncMock(return_value=None)
        mock_cache.get_seen_user_ids = AsyncMock(return_value=[])
        
        mock_current = MagicMock(id=1, user_id=1, embedding=None)
        mock_repos['profile'].get_by_user_id = AsyncMock(return_value=mock_current)
        
        mock_repos['profile'].get_similar_profiles = AsyncMock(return_value=[])
        mock_repos['profile'].get_random_profiles = AsyncMock(return_value=[])
        
        with pytest.raises(NoMoreProfilesException):
            await profile_service.get_next_profile(user_id=1)


@pytest.mark.asyncio
async def test_profile_to_dict(profile_service):
    mock_profile = MagicMock(
        spec=['id', 'user_id', 'name', 'description', 'gender', 'age', 'media', 'is_active', 'created_at', 'updated_at'],
        id=1,
        user_id=2,
        description="Desc",
        gender=GenderEnum.female,
        age=25,
        media=[{"type": "photo", "file_id": "abc123"}],
        is_active=True,
        created_at="2024-01-01",
        updated_at="2024-01-02"
    )
    mock_profile.name = "Test"
    
    result = profile_service._profile_to_dict(mock_profile)
    
    assert result['id'] == 1
    assert result['user_id'] == 2
    assert result['name'] == "Test"
    assert result['gender'] == "female"
    assert result['media'] == [{"type": "photo", "file_id": "abc123"}]
    assert result['is_active'] == True
