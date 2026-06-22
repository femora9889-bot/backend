from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review
from app.models.store import Store, StoreCategory
from app.models.wishlist import StoreWishlist
from app.repositories.base import BaseRepository


class StoreRepository(BaseRepository[Store]):
    def __init__(self, db: AsyncSession):
        super().__init__(Store, db)

    async def list_active(
        self,
        category_id: int | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Store], int]:
        query = select(Store).where(Store.is_active == True)

        if category_id:
            query = query.join(StoreCategory).where(StoreCategory.category_id == category_id)
        if search:
            query = query.where(Store.name.ilike(f"%{search}%"))

        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()

        result = await self.db.execute(query.offset(offset).limit(limit))
        return result.scalars().all(), total

    async def get_with_details(self, store_id: str) -> Store | None:
        result = await self.db.execute(
            select(Store)
            .where(Store.id == store_id)
            .options(selectinload(Store.category_links).selectinload(StoreCategory.category))
        )
        return result.scalar_one_or_none()

    async def get_avg_rating(self, store_id: str) -> float | None:
        result = await self.db.execute(
            select(func.avg(Review.rating))
            .join(Review.product)
            .where(Review.product.has(store_id=store_id))
        )
        return result.scalar_one_or_none()

    async def is_wishlisted(self, user_id: str, store_id: str) -> bool:
        result = await self.db.execute(
            select(StoreWishlist).where(
                StoreWishlist.user_id == user_id,
                StoreWishlist.store_id == store_id,
            )
        )
        return result.scalar_one_or_none() is not None
