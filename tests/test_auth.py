import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "name": "أمل",
        "phone": "+963991234567",
        "password": "password123",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_phone(client: AsyncClient):
    payload = {"name": "أمل", "phone": "+963991234567", "password": "password123"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "name": "أمل", "phone": "+963991234567", "password": "password123"
    })
    response = await client.post("/api/v1/auth/login", json={
        "phone": "+963991234567", "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "name": "أمل", "phone": "+963991234567", "password": "password123"
    })
    response = await client.post("/api/v1/auth/login", json={
        "phone": "+963991234567", "password": "wrongpassword"
    })
    assert response.status_code == 401
