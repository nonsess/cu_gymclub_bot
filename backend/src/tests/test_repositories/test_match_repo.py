import pytest
from src.repositories.match import MatchRepository
from src.repositories.user import UserRepository
from src.repositories.base import BaseRepository
from src.models.match import Match


@pytest.mark.asyncio
async def test_create_match(session):
    user_repo = UserRepository(session)
    user1 = await user_repo.create(telegram_id="900001")
    user2 = await user_repo.create(telegram_id="900002")
    
    repo = MatchRepository(session)
    match = await repo.create_match(user1.id, user2.id)
    
    assert match is not None
    assert match.user1_id < match.user2_id
    assert {match.user1_id, match.user2_id} == {user1.id, user2.id}
    assert match.is_notified == False


@pytest.mark.asyncio
async def test_create_match_id_normalization(session):
    user_repo = UserRepository(session)
    user1 = await user_repo.create(telegram_id="900003")
    user2 = await user_repo.create(telegram_id="900004")
    
    repo = MatchRepository(session)
    
    match = await repo.create_match(user2.id, user1.id)
    
    assert match.user1_id < match.user2_id
    assert match.user1_id == user1.id
    assert match.user2_id == user2.id


@pytest.mark.asyncio
async def test_get_match_by_base_repo(session):
    user_repo = UserRepository(session)
    user1 = await user_repo.create(telegram_id="900005")
    user2 = await user_repo.create(telegram_id="900006")
    
    match_repo = MatchRepository(session)
    match = await match_repo.create_match(user1.id, user2.id)
    
    base_repo = BaseRepository(Match, session)
    found = await base_repo.get(match.id)
    
    assert found is not None
    assert found.id == match.id


@pytest.mark.asyncio
async def test_get_all_matches(session):
    user_repo = UserRepository(session)
    match_repo = MatchRepository(session)
    
    for i in range(3):
        u1 = await user_repo.create(telegram_id=f"9000{10+i}")
        u2 = await user_repo.create(telegram_id=f"9000{20+i}")
        await match_repo.create_match(u1.id, u2.id)
    
    base_repo = BaseRepository(Match, session)
    matches = await base_repo.get_all(limit=10)
    
    assert len(matches) >= 3


@pytest.mark.asyncio
async def test_delete_match(session):
    user_repo = UserRepository(session)
    user1 = await user_repo.create(telegram_id="900008")
    user2 = await user_repo.create(telegram_id="900009")
    
    match_repo = MatchRepository(session)
    match = await match_repo.create_match(user1.id, user2.id)
    
    await match_repo.delete(match)
    await session.commit()
    
    base_repo = BaseRepository(Match, session)
    found = await base_repo.get(match.id)
    assert found is None


@pytest.mark.asyncio
async def test_update_match_is_notified(session):
    user_repo = UserRepository(session)
    user1 = await user_repo.create(telegram_id="900010")
    user2 = await user_repo.create(telegram_id="900011")
    
    match_repo = MatchRepository(session)
    match = await match_repo.create_match(user1.id, user2.id)
    
    await match_repo.update(match, is_notified=True)
    await session.refresh(match)
    
    assert match.is_notified == True