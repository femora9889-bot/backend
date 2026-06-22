from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.store import Store
from app.models.wishlist import StoreWishlist, Wishlist
from app.repositories.base import BaseRepository


class WishlistRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_products(self, user_id: str) -> list[Wishlist]:
        result = await self.db.execute(
            select(Wishlist)
            .where(Wishlist.user_id == user_id)
            .options(selectinload(Wishlist.product).selectinload(Product.images))
            .order_by(Wishlist.created_at.desc())
        )
        return result.scalars().all()

    async def get_item(self, user_id: str, product_id: str) -> Wishlist | None:
        result = await self.db.execute(
            select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def add_product(self, user_id: str, product_id: str) -> Wishlist:
        item = Wishlist(user_id=user_id, product_id=product_id)
        self.db.add(item)
        await self.db.commit()
        return item

    async def remove_product(self, user_id: str, product_id: str) -> bool:
        item = await self.get_item(user_id, product_id)
        if not item:
            return False
        await self.db.delete(item)
        await self.db.commit()
        return True

    async def get_user_stores(self, user_id: str) -> list[StoreWishlist]:
        result = await self.db.execute(
            select(StoreWishlist)
            .where(StoreWishlist.user_id == user_id)
            .options(selectinload(StoreWishlist.store))
            .order_by(StoreWishlist.created_at.desc())
        )
        return result.scalars().all()

    async def get_store_item(self, user_id: str, store_id: str) -> StoreWishlist | None:
        result = await self.db.execute(
            select(StoreWishlist).where(
                StoreWishlist.user_id == user_id,
                StoreWishlist.store_id == store_id,
            )
        )
        return result.scalar_one_or_none()

    async def toggle_store(self, user_id: str, store_id: str) -> bool:
        item = await self.get_store_item(user_id, store_id)
        if item:
            await self.db.delete(item)
            await self.db.commit()
            return False
        self.db.add(StoreWishlist(user_id=user_id, store_id=store_id))
        await self.db.commit()
        return True
