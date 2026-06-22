from pydantic import BaseModel

from app.schemas.product import ProductListItem
from app.schemas.store import StoreListItem


class WishlistResponse(BaseModel):
    products: list[ProductListItem] = []


class StoreWishlistResponse(BaseModel):
    stores: list[StoreListItem] = []
