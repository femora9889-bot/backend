import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.models.order import OrderStatus
from app.models.product import Product, ProductVariant
from app.models.store import Store


async def seed_data(db: AsyncSession, user_id: str) -> tuple[str, str, str]:
    store = Store(
        id="store1", owner_id="admin",
        name="بوتيك الأميرة", city="دمشق",
        address="شارع بغداد", phone="0991234567",
    )
    db.add(store)

    product = Product(id="prod1", store_id="store1", name="فستان", base_price=5000)
    db.add(product)

    variant = ProductVariant(
        id="var1", product_id="prod1",
        color="أزرق", size="M",
        stock_quantity=5, is_available=True,
    )
    db.add(variant)

    address = Address(
        id="addr1", user_id=user_id,
        label="البيت", city="دمشق",
        area="المزة", is_default=True,
    )
    db.add(address)
    await db.commit()
    return "var1", "addr1", "store1"


async def get_user_id(client: AsyncClient, auth_headers: dict) -> str:
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    return response.json()["id"]


@pytest.mark.asyncio
async def test_add_address(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/addresses",
        json={"label": "البيت", "city": "دمشق", "area": "المزة"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["city"] == "دمشق"


@pytest.mark.asyncio
async def test_create_order_from_cart(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    user_id = await get_user_id(client, auth_headers)
    variant_id, address_id, _ = await seed_data(db, user_id)

    await client.post(
        "/api/v1/cart/items",
        json={"product_variant_id": variant_id, "quantity": 2},
        headers=auth_headers,
    )

    response = await client.post(
        "/api/v1/orders",
        json={"address_id": address_id},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["store_orders"]) == 1
    assert data["store_orders"][0]["status"] == OrderStatus.pending
    assert data["store_orders"][0]["subtotal"] == 10000.0


@pytest.mark.asyncio
async def test_order_clears_cart(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    user_id = await get_user_id(client, auth_headers)
    variant_id, address_id, _ = await seed_data(db, user_id)

    await client.post(
        "/api/v1/cart/items",
        json={"product_variant_id": variant_id, "quantity": 1},
        headers=auth_headers,
    )
    await client.post("/api/v1/orders", json={"address_id": address_id}, headers=auth_headers)

    cart_response = await client.get("/api/v1/cart", headers=auth_headers)
    assert cart_response.json()["total"] == 0


@pytest.mark.asyncio
async def test_create_order_empty_cart(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    user_id = await get_user_id(client, auth_headers)
    _, address_id, _ = await seed_data(db, user_id)

    response = await client.post(
        "/api/v1/orders",
        json={"address_id": address_id},
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    user_id = await get_user_id(client, auth_headers)
    variant_id, address_id, _ = await seed_data(db, user_id)

    await client.post(
        "/api/v1/cart/items",
        json={"product_variant_id": variant_id, "quantity": 1},
        headers=auth_headers,
    )
    await client.post("/api/v1/orders", json={"address_id": address_id}, headers=auth_headers)

    response = await client.get("/api/v1/orders", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_cancel_order(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    user_id = await get_user_id(client, auth_headers)
    variant_id, address_id, _ = await seed_data(db, user_id)

    await client.post(
        "/api/v1/cart/items",
        json={"product_variant_id": variant_id, "quantity": 1},
        headers=auth_headers,
    )
    order_response = await client.post(
        "/api/v1/orders",
        json={"address_id": address_id},
        headers=auth_headers,
    )
    order_store_id = order_response.json()["store_orders"][0]["id"]

    cancel_response = await client.post(
        f"/api/v1/orders/stores/{order_store_id}/cancel",
        headers=auth_headers,
    )
    assert cancel_response.status_code == 200
