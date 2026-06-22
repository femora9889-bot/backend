from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review, ReviewHelpful
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, db: AsyncSession):
        super().__init__(Review, db)

    async def get_product_reviews(self, product_id: str, offset: int = 0, limit: int = 20) -> list[Review]:
        result = await self.db.execute(
            select(Review)
            .where(Review.product_id == product_id)
            .options(selectinload(Review.user))
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_user_product_order(self, user_id: str, product_id: str, order_store_id: str) -> Review | None:
        result = await self.db.execute(
            select(Review).where(
                Review.user_id == user_id,
                Review.product_id == product_id,
                Review.order_store_id == order_store_id,
            )
        )
        return result.scalar_one_or_none()

    async def has_purchased(self, user_id: str, product_id: str) -> bool:
        from app.models.order import OrderItem, OrderStore
        result = await self.db.execute(
            select(OrderItem)
            .join(OrderStore)
            .join(OrderItem.variant)
            .where(
                OrderStore.order.has(user_id=user_id),
                OrderStore.status == "delivered",
            )
        )
        return result.scalar_one_or_none() is not None

    async def mark_helpful(self, review_id: str, user_id: str) -> bool:
        existing = await self.db.execute(
            select(ReviewHelpful).where(
                ReviewHelpful.review_id == review_id,
                ReviewHelpful.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            return False
        self.db.add(ReviewHelpful(review_id=review_id, user_id=user_id))
        await self.db.commit()
        return True
