from pydantic import BaseModel


class CartItemAdd(BaseModel):
    product_variant_id: str
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: str
    product_variant_id: str
    product_name: str
    color: str
    size: str
    price: float
    original_price: float | None
    image_url: str | None
    store_id: str
    store_name: str
    quantity: int
    stock_quantity: int

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    items_by_store: dict[str, list[CartItemResponse]] = {}
    total: float = 0
