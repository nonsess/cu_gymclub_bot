import pytest


@pytest.mark.asyncio
async def test_register_user_success(client, session):
    response = await client.post(
        "/users/register",
        json={
            "telegram_id": "123456789",
            "username": "@newuser",
            "first_name": "New"
        }
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_user_idempotent(client, session):
    response1 = await client.post(
        "/users/register",
        json={
            "telegram_id": "999888777",
            "username": "@existing",
            "first_name": "Existing"
        }
    )
    assert response1.status_code == 200
    
    response2 = await client.post(
        "/users/register",
        json={
            "telegram_id": "999888777",
            "username": "@updated",
            "first_name": "Updated"
        }
    )
    assert response2.status_code == 200
    
    from src.repositories.user import UserRepository
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id("999888777")
    assert user is not None


@pytest.mark.asyncio
async def test_register_user_validation_error(client):
    response = await client.post(
        "/users/register",
        json={
            "telegram_id": "",
            "username": "@invalid",
            "first_name": "Invalid"
        }
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_user_minimal_data(client, session):
    response = await client.post(
        "/users/register",
        json={
            "telegram_id": "555666777"
        }
    )
    
    assert response.status_code == 200
    
    from src.repositories.user import UserRepository
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id("555666777")
    assert user is not None
    assert user.telegram_id == "555666777"