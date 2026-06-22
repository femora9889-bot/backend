from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.wishlist_repo import WishlistRepository
from app.schemas.wishlist import StoreWishlistResponse, WishlistResponse
from app.schemas.product import ProductListItem
from app.schemas.store import StoreListItem


class WishlistService:
    def __init__(self, db: AsyncSession):
        self.repo = WishlistRepository(db)

    async def get_products(self, user: User) -> WishlistResponse:
        items = await self.repo.get_user_products(user.id)
        products = []
        for item in items:
            p = item.product
            primary_img = next((img.url for img in p.images if img.is_primary), None)
            products.append(ProductListItem(
                id=p.id,
                name=p.name,
                base_price=float(p.base_price),
                primary_image=primary_img,
                store_name="",
                store_id=p.store_id,
                is_wishlisted=True,
            ))
        return WishlistResponse(products=products)

    async def toggle_product(self, user: User, product_id: str) -> WishlistResponse:
        item = await self.repo.get_item(user.id, product_id)
        if item:
            await self.repo.remove_product(user.id, product_id)
        else:
            await self.repo.add_product(user.id, product_id)
        return await self.get_products(user)

    async def toggle_store(self, user: User, store_id: str) -> StoreWishlistResponse:
        await self.repo.toggle_store(user.id, store_id)
        return await self.get_stores(user)

    async def get_stores(self, user: User) -> StoreWishlistResponse:
        items = await self.repo.get_user_stores(user.id)
        stores = [
            StoreListItem(
                id=item.store.id,
                name=item.store.name,
                logo_url=item.store.logo_url,
                cover_url=item.store.cover_url,
                city=item.store.city,
                is_verified=item.store.is_verified,
                is_wishlisted=True,
            )
            for item in items
        ]
        return StoreWishlistResponse(stores=stores)
