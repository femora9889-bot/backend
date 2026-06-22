import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductImage, ProductVariant, SizeGuide
from app.models.store import Store
from app.models.user import BodyShape


async def seed_products(db: AsyncSession):
    store = Store(
        id="store1", owner_id="admin",
        name="بوتيك الأميرة", city="دمشق",
        address="شارع بغداد", phone="0991234567",
    )
    db.add(store)

    for i in range(3):
        p = Product(id=f"prod{i}", store_id="store1", name=f"فستان {i}", base_price=5000 + i * 1000)
        db.add(p)
        db.add(ProductImage(product_id=f"prod{i}", url=f"https://example.com/img{i}.jpg", is_primary=True, display_order=0))
        db.add(ProductVariant(product_id=f"prod{i}", color="أحمر", size="M", stock_quantity=5))
        db.add(SizeGuide(product_id=f"prod{i}", size_label="M", bust_cm=88, waist_cm=70, hips_cm=94))

    await db.commit()


@pytest.mark.asyncio
async def test_list_products_by_store(client: AsyncClient, db: AsyncSession):
    await seed_products(db)
    response = await client.get("/api/v1/products?store_id=store1")
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_search_products(client: AsyncClient, db: AsyncSession):
    await seed_products(db)
    response = await client.get("/api/v1/products?search=فستان")
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_get_product_detail(client: AsyncClient, db: AsyncSession):
    await seed_products(db)
    response = await client.get("/api/v1/products/prod0")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "فستان 0"
    assert len(data["variants"]) == 1
    assert len(data["size_guides"]) == 1


@pytest.mark.asyncio
async def test_get_product_with_fit_score(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    await seed_products(db)

    await client.put(
        "/api/v1/users/me/measurements",
        json={
            "height_cm": 165, "weight_kg": 60,
            "body_shape": BodyShape.hourglass,
            "bust_cm": 88, "waist_cm": 70, "hips_cm": 94,
        },
        headers=auth_headers,
    )

    response = await client.get(
        "/api/v1/products/prod0?selected_size=M",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["fit_score"] == 100


@pytest.mark.asyncio
async def test_product_not_found(client: AsyncClient):
    response = await client.get("/api/v1/products/nonexistent")
    assert response.status_code == 404
