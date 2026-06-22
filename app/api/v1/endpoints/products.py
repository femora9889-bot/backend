from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_optional_user
from app.models.user import User
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import MeasurementsRepository
from app.schemas.product import ProductFiltersResponse, ProductListItem, ProductResponse
from app.services.fit_service import calculate_fit

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[ProductListItem])
async def list_products(
    category_id: int | None = Query(None),
    store_id: str | None = Query(None),
    search: str | None = Query(None),
    min_price: float | None = Query(None),
    max_price: float | None = Query(None),
    color: str | None = Query(None),
    size: str | None = Query(None),
    fabric: str | None = Query(None),
    product_type: str | None = Query(None),
    has_discount: bool | None = Query(None),
    in_stock: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone, timedelta
    repo = ProductRepository(db)

    products, _ = await repo.list_with_filters(
        category_id=category_id,
        store_id=store_id,
        search=search,
        min_price=min_price,
        max_price=max_price,
        color=color,
        size=size,
        fabric=fabric,
        product_type=product_type,
        has_discount=has_discount,
        in_stock=in_stock,
        offset=(page - 1) * page_size,
        limit=page_size,
    )

    measurements = None
    if user:
        m_repo = MeasurementsRepository(db)
        measurements = await m_repo.get_by_user(user.id)

    result = []
    new_threshold = datetime.now(timezone.utc) - timedelta(days=14)

    for p in products:
        avg, _ = await repo.get_avg_rating(p.id)
        is_wishlisted = await repo.is_wishlisted(user.id, p.id) if user else False
        primary_img = next((img.url for img in p.images if img.is_primary), None)

        fit_score = None
        if measurements:
            guides = await repo.get_size_guides(p.id)
            if guides:
                first_size = p.variants[0].size if p.variants else None
                if first_size:
                    fit = calculate_fit(measurements, guides, first_size)
                    fit_score = fit.score

        has_disc = any(v.original_price is not None for v in p.variants)

        result.append(ProductListItem(
            id=p.id,
            name=p.name,
            base_price=float(p.base_price),
            primary_image=primary_img,
            store_name="",
            store_id=p.store_id,
            category_id=p.category_id,
            product_type=p.product_type,
            fabric=p.fabric,
            avg_rating=round(float(avg), 1) if avg else None,
            is_new=p.created_at.replace(tzinfo=timezone.utc) > new_threshold if p.created_at else False,
            has_discount=has_disc,
            fit_score=fit_score,
            is_wishlisted=is_wishlisted,
        ))
    return result


@router.get("/filters", response_model=ProductFiltersResponse)
async def get_product_filters(
    category_id: int | None = Query(None),
    store_id: str | None = Query(None),
    search: str | None = Query(None),
    min_price: float | None = Query(None),
    max_price: float | None = Query(None),
    color: str | None = Query(None),
    size: str | None = Query(None),
    fabric: str | None = Query(None),
    product_type: str | None = Query(None),
    has_discount: bool | None = Query(None),
    in_stock: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone, timedelta
    repo = ProductRepository(db)

    products, total = await repo.list_with_filters(
        category_id=category_id,
        store_id=store_id,
        search=search,
        min_price=min_price,
        max_price=max_price,
        color=color,
        size=size,
        fabric=fabric,
        product_type=product_type,
        has_discount=has_discount,
        in_stock=in_stock,
        offset=(page - 1) * page_size,
        limit=page_size,
    )

    measurements = None
    if user:
        m_repo = MeasurementsRepository(db)
        measurements = await m_repo.get_by_user(user.id)

    items = []
    new_threshold = datetime.now(timezone.utc) - timedelta(days=14)
    for p in products:
        avg, _ = await repo.get_avg_rating(p.id)
        is_wishlisted = await repo.is_wishlisted(user.id, p.id) if user else False
        primary_img = next((img.url for img in p.images if img.is_primary), None)
        fit_score = None
        if measurements:
            guides = await repo.get_size_guides(p.id)
            if guides:
                first_size = p.variants[0].size if p.variants else None
                if first_size:
                    fit = calculate_fit(measurements, guides, first_size)
                    fit_score = fit.score
        has_disc = any(v.original_price is not None for v in p.variants)
        items.append(ProductListItem(
            id=p.id,
            name=p.name,
            base_price=float(p.base_price),
            primary_image=primary_img,
            store_name="",
            store_id=p.store_id,
            category_id=p.category_id,
            product_type=p.product_type,
            fabric=p.fabric,
            avg_rating=round(float(avg), 1) if avg else None,
            is_new=p.created_at.replace(tzinfo=timezone.utc) > new_threshold if p.created_at else False,
            has_discount=has_disc,
            fit_score=fit_score,
            is_wishlisted=is_wishlisted,
        ))

    return ProductFiltersResponse(products=items, total=total)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    selected_size: str | None = Query(None),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.exceptions import NotFoundError
    from app.schemas.product import ProductImageResponse, ProductVariantResponse, SizeGuideResponse

    repo = ProductRepository(db)
    product = await repo.get_with_details(product_id)
    if not product:
        raise NotFoundError("Product not found")

    avg, count = await repo.get_avg_rating(product_id)
    is_wishlisted = await repo.is_wishlisted(user.id, product_id) if user else False

    fit_score = None
    fit_assessment = None
    if user and selected_size:
        m_repo = MeasurementsRepository(db)
        measurements = await m_repo.get_by_user(user.id)
        if measurements and product.size_guides:
            fit = calculate_fit(measurements, product.size_guides, selected_size)
            fit_score = fit.score
            fit_assessment = fit.warning or fit.assessment

    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        base_price=float(product.base_price),
        is_available=product.is_available,
        store_id=product.store_id,
        store_name="",
        images=[ProductImageResponse.model_validate(img) for img in product.images],
        variants=[ProductVariantResponse.model_validate(v) for v in product.variants],
        size_guides=[SizeGuideResponse.model_validate(sg) for sg in product.size_guides],
        avg_rating=round(float(avg), 1) if avg else None,
        review_count=count,
        fit_score=fit_score,
        fit_assessment=fit_assessment,
        is_wishlisted=is_wishlisted,
    )
