from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_optional_user
from app.models.user import User
from app.repositories.store_repo import StoreRepository
from app.schemas.store import CategoryResponse, StoreListItem, StoreResponse

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.get("", response_model=list[StoreListItem])
async def list_stores(
    category_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    repo = StoreRepository(db)
    stores, _ = await repo.list_active(category_id, search, offset=(page - 1) * size, limit=size)
    result = []
    for store in stores:
        is_wishlisted = await repo.is_wishlisted(user.id, store.id) if user else False
        avg_rating = await repo.get_avg_rating(store.id)
        result.append(StoreListItem(
            id=store.id,
            name=store.name,
            logo_url=store.logo_url,
            cover_url=store.cover_url,
            city=store.city,
            is_verified=store.is_verified,
            avg_rating=round(float(avg_rating), 1) if avg_rating else None,
            is_wishlisted=is_wishlisted,
        ))
    return result


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: str,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.exceptions import NotFoundError
    repo = StoreRepository(db)
    store = await repo.get_with_details(store_id)
    if not store:
        raise NotFoundError("Store not found")

    avg_rating = await repo.get_avg_rating(store_id)
    is_wishlisted = await repo.is_wishlisted(user.id, store_id) if user else False

    categories = [link.category for link in store.category_links]
    from app.schemas.store import CategoryResponse
    return StoreResponse(
        id=store.id,
        name=store.name,
        logo_url=store.logo_url,
        cover_url=store.cover_url,
        description=store.description,
        city=store.city,
        address=store.address,
        phone=store.phone,
        is_verified=store.is_verified,
        categories=[CategoryResponse.model_validate(c) for c in categories],
        avg_rating=round(float(avg_rating), 1) if avg_rating else None,
        is_wishlisted=is_wishlisted,
    )
