import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from src.models.base import BaseModel
from src.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://gymblubbot:verystrongpassword@db:5432/gymbot_db_test"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    admin_url = "postgresql+asyncpg://gymblubbot:verystrongpassword@db:5432/gymbot_db"
    admin_engine = create_async_engine(admin_url, echo=False, isolation_level="AUTOCOMMIT")
    
    try:
        async with admin_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = 'gymbot_db_test'")
            )
            if not exists:
                await conn.execute(text("CREATE DATABASE gymbot_db_test"))
                
                await conn.execute(
                    text("CREATE EXTENSION IF NOT EXISTS vector"),
                    execution_options={"isolation_level": "AUTOCOMMIT"}
                )
    except Exception as e:
        print(f"Warning: Could not setup test DB: {e}")
    finally:
        await admin_engine.dispose()
    
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(BaseModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(test_engine):
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(session):    
    async def override_get_db():
        yield session
    
    app.dependency_overrides = {}
    from src.core import deps
    if hasattr(deps, 'get_db'):
        app.dependency_overrides[deps.get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides = {}


@pytest.fixture
def mock_cache():
    with patch('src.services.profile.cache') as mock_profile_cache, \
         patch('src.services.action.cache') as mock_action_cache, \
         patch('src.services.admin.cache') as mock_admin_cache:
        
        for mock in [mock_profile_cache, mock_action_cache, mock_admin_cache]:
            mock.add_seen_user_id = AsyncMock()
            mock.get_seen_user_ids = AsyncMock(return_value=[])
            mock.invalidate_profile = AsyncMock()
            mock.add_seen = AsyncMock()
            mock.get_seen = AsyncMock(return_value=[])
            mock.pop_from_queue = AsyncMock(return_value=None)
            mock.get_cached_profile = AsyncMock(return_value=None)
            mock.fill_queue = AsyncMock()
            mock.cache_profile = AsyncMock()
        
        yield {
            'profile': mock_profile_cache,
            'action': mock_action_cache,
            'admin': mock_admin_cache,
        }


@pytest.fixture
def admin_headers():
    return {
        "X-Telegram-ID": "121231231",
    }


@pytest.fixture
def user_headers():
    return {
        "X-Telegram-ID": "123456789",
    }