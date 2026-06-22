from pydantic import BaseModel


class PriceRange(BaseModel):
    min: float
    max: float


class StoreOption(BaseModel):
    id: str
    name: str


class ProductFiltersResponse(BaseModel):
    products: list["ProductListItem"] = []
    total: int = 0


class ProductImageResponse(BaseModel):
    id: str
    url: str
    is_primary: bool

    model_config = {"from_attributes": True}


class ProductVariantResponse(BaseModel):
    id: str
    color: str
    color_hex: str | None
    size: str
    stock_quantity: int
    original_price: float | None
    price_override: float | None
    is_available: bool

    model_config = {"from_attributes": True}


class SizeGuideResponse(BaseModel):
    size_label: str
    bust_cm: float | None
    waist_cm: float | None
    hips_cm: float | None
    length_cm: float | None

    model_config = {"from_attributes": True}


class ProductListItem(BaseModel):
    id: str
    name: str
    base_price: float
    primary_image: str | None = None
    store_name: str
    store_id: str
    category_id: int | None = None
    product_type: str | None = None
    fabric: str | None = None
    avg_rating: float | None = None
    is_new: bool = False
    has_discount: bool = False
    fit_score: float | None = None
    is_wishlisted: bool = False

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str | None
    base_price: float
    is_available: bool
    store_id: str
    store_name: str
    category_id: int | None = None
    product_type: str | None = None
    fabric: str | None = None
    images: list[ProductImageResponse] = []
    variants: list[ProductVariantResponse] = []
    size_guides: list[SizeGuideResponse] = []
    avg_rating: float | None = None
    review_count: int = 0
    fit_score: float | None = None
    fit_assessment: str | None = None
    is_wishlisted: bool = False

    model_config = {"from_attributes": True}
