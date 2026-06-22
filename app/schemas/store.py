from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: int
    name: str
    name_ar: str

    model_config = {"from_attributes": True}


class StoreListItem(BaseModel):
    id: str
    name: str
    logo_url: str | None
    cover_url: str | None
    city: str
    is_verified: bool
    avg_rating: float | None = None
    is_wishlisted: bool = False

    model_config = {"from_attributes": True}


class StoreResponse(BaseModel):
    id: str
    name: str
    logo_url: str | None
    cover_url: str | None
    description: str | None
    city: str
    address: str
    phone: str
    is_verified: bool
    categories: list[CategoryResponse] = []
    avg_rating: float | None = None
    review_count: int = 0
    is_wishlisted: bool = False

    model_config = {"from_attributes": True}
