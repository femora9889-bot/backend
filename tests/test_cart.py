import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductVariant
from app.models.store import Store
from app.models.user import User


async def seed_store_and_product(db: AsyncSession) -> tuple[str, str]:
    store = Store(
        id="store1", owner_id="admin",
        name="بوتيك الأميرة", city="دمشق",
        address="شارع بغداد", phone="0991234567",
    )
    db.add(store)

    product = Product(
        id="prod1", store_id="store1",
        name="فستان سهرة", base_price=7500,
    )
    db.add(product)

    variant = ProductVariant(
        id="var1", product_id="prod1",
        color="وردي", size="M",
        stock_quantity=10, is_available=True,
    )
    db.add(variant)
    await db.commit()
    return "prod1", "var1"


@pytest.mark.asyncio
async def test_get_empty_cart(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/cart", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_add_item_to_cart(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    await seed_store_and_product(db)
    response = await client.post(
        "/api/v1/cart/items",
        json={"product_variant_id": "var1", "quantity": 2},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total"] == 15000.0
    assert "store1" in data["items_by_store"]


@pytest.mark.asyncio
async def test_add_item_exceeds_stock(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    await seed_store_and_product(db)
    response = await client.post(
        "/api/v1/cart/items",
        json={"product_variant_id": "var1", "quantity": 99},
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_item_quantity(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    await seed_store_and_product(db)
    await client.post(
        "/api/v1/cart/items",
        json={"product_variant_id": "var1", "quantity": 1},
        headers=auth_headers,
    )
    response = await client.patch(
        "/api/v1/cart/items/var1",
        json={"quantity": 3},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 22500.0


@pytest.mark.asyncio
async def test_remove_item(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    await seed_store_and_product(db)
    await client.post(
        "/api/v1/cart/items",
        json={"product_variant_id": "var1", "quantity": 1},
        headers=auth_headers,
    )
    response = await client.delete("/api/v1/cart/items/var1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_cart_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/cart")
    assert response.status_code == 403
