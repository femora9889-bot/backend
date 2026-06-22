from pydantic import BaseModel, field_validator


class ReviewCreate(BaseModel):
    order_store_id: str
    rating: int
    comment: str | None = None
    image_url: str | None = None
    is_anonymous: bool = False

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewResponse(BaseModel):
    id: str
    rating: int
    comment: str | None
    image_url: str | None
    is_anonymous: bool
    helpful_count: int
    reviewer_name: str | None
    reviewer_image: str | None
    created_at: str

    model_config = {"from_attributes": True}
