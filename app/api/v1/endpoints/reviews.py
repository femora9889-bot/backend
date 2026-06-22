from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.infrastructure.storage.cloudinary_client import upload_image
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/products", tags=["Reviews"])


@router.get("/{product_id}/reviews", response_model=list[ReviewResponse])
async def get_reviews(
    product_id: str,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    return await ReviewService(db).get_product_reviews(product_id, offset=(page - 1) * 20)


@router.post("/{product_id}/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(
    product_id: str,
    data: ReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReviewService(db).create(user, product_id, data)


@router.post("/{product_id}/reviews/{review_id}/helpful")
async def mark_helpful(
    product_id: str,
    review_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReviewService(db).mark_helpful(user, review_id)


@router.post("/{product_id}/reviews/{review_id}/image")
async def upload_review_image(
    product_id: str,
    review_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.review_repo import ReviewRepository
    from app.core.exceptions import ForbiddenError, NotFoundError
    repo = ReviewRepository(db)
    review = await repo.get_by_id(review_id)
    if not review:
        raise NotFoundError("Review not found")
    if review.user_id != user.id:
        raise ForbiddenError()
    content = await file.read()
    url = await upload_image(content, "review", public_id=f"review_{review_id}")
    review.image_url = url
    await repo.save(review)
    return {"image_url": url}
