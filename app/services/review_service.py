from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.review import Review
from app.models.user import User
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewResponse


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.repo = ReviewRepository(db)
        self.order_repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)

    async def create(self, user: User, product_id: str, data: ReviewCreate) -> ReviewResponse:
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found")

        order_store = await self.order_repo.get_order_store(data.order_store_id)
        if not order_store:
            raise NotFoundError("Order not found")

        order = await self.order_repo.get_by_id(order_store.order_id)
        if order.user_id != user.id:
            raise BadRequestError("You can only review products you purchased")

        from app.models.order import OrderStatus
        if order_store.status != OrderStatus.delivered:
            raise BadRequestError("You can only review delivered orders")

        existing = await self.repo.get_by_user_product_order(user.id, product_id, data.order_store_id)
        if existing:
            raise ConflictError("You have already reviewed this product for this order")

        review = Review(
            user_id=user.id,
            product_id=product_id,
            order_store_id=data.order_store_id,
            rating=data.rating,
            comment=data.comment,
            image_url=data.image_url,
            is_anonymous=data.is_anonymous,
        )
        await self.repo.save(review)
        return self._to_response(review, user)

    async def get_product_reviews(self, product_id: str, offset: int = 0, limit: int = 20) -> list[ReviewResponse]:
        reviews = await self.repo.get_product_reviews(product_id, offset, limit)
        return [self._to_response(r, r.user) for r in reviews]

    async def mark_helpful(self, user: User, review_id: str) -> dict:
        added = await self.repo.mark_helpful(review_id, user.id)
        return {"message": "Marked as helpful" if added else "Already marked"}

    def _to_response(self, review: Review, user) -> ReviewResponse:
        return ReviewResponse(
            id=review.id,
            rating=review.rating,
            comment=review.comment,
            image_url=review.image_url,
            is_anonymous=review.is_anonymous,
            helpful_count=review.helpful_count,
            reviewer_name=None if review.is_anonymous else user.name,
            reviewer_image=None if review.is_anonymous else user.profile_image,
            created_at=review.created_at.isoformat(),
        )
