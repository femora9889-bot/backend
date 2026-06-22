from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product, ProductVariant
from app.models.store import Store
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[Cart]):
    def __init__(self, db: AsyncSession):
        super().__init__(Cart, db)

    async def get_by_user(self, user_id: str) -> Cart | None:
        result = await self.db.execute(
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(
                selectinload(Cart.items).selectinload(CartItem.variant).selectinload(
                    ProductVariant.product
                ).options(
                    selectinload(Product.images),
                    selectinload(Product.store),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_item(self, cart_id: str, variant_id: str) -> CartItem | None:
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.product_variant_id == variant_id,
            )
        )
        return result.scalar_one_or_none()
