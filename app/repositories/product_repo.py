from sqlalchemy import distinct, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductVariant, SizeGuide
from app.models.review import Review
from app.models.store import Store
from app.models.wishlist import Wishlist
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: AsyncSession):
        super().__init__(Product, db)

    async def list_with_filters(
        self,
        category_id: int | None = None,
        store_id: str | None = None,
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        color: str | None = None,
        size: str | None = None,
        fabric: str | None = None,
        product_type: str | None = None,
        has_discount: bool | None = None,
        in_stock: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Product], int]:
        query = select(Product).where(Product.is_available == True)

        if category_id:
            query = query.where(Product.category_id == category_id)
        if store_id:
            query = query.where(Product.store_id == store_id)
        if search:
            query = query.where(Product.name.ilike(f"%{search}%"))
        if min_price is not None:
            query = query.where(Product.base_price >= min_price)
        if max_price is not None:
            query = query.where(Product.base_price <= max_price)
        if fabric:
            query = query.where(Product.fabric.ilike(f"%{fabric}%"))
        if product_type:
            query = query.where(Product.product_type == product_type)
        if color:
            query = query.where(
                exists().where(
                    ProductVariant.product_id == Product.id,
                    ProductVariant.color.ilike(f"%{color}%"),
                )
            )
        if size:
            query = query.where(
                exists().where(
                    ProductVariant.product_id == Product.id,
                    ProductVariant.size == size,
                )
            )
        if has_discount is True:
            query = query.where(
                exists().where(
                    ProductVariant.product_id == Product.id,
                    ProductVariant.original_price.isnot(None),
                )
            )
        if in_stock is True:
            query = query.where(
                exists().where(
                    ProductVariant.product_id == Product.id,
                    ProductVariant.stock_quantity > 0,
                )
            )

        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()

        result = await self.db.execute(
            query.options(
                selectinload(Product.images),
                selectinload(Product.variants),
            ).offset(offset).limit(limit)
        )
        return result.scalars().all(), total

    async def get_filter_options(
        self,
        category_id: int | None = None,
        store_id: str | None = None,
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        fabric: str | None = None,
        product_type: str | None = None,
    ) -> dict:
        base = select(Product.id).where(Product.is_available == True)
        if category_id:
            base = base.where(Product.category_id == category_id)
        if store_id:
            base = base.where(Product.store_id == store_id)
        if search:
            base = base.where(Product.name.ilike(f"%{search}%"))
        if min_price is not None:
            base = base.where(Product.base_price >= min_price)
        if max_price is not None:
            base = base.where(Product.base_price <= max_price)
        if fabric:
            base = base.where(Product.fabric.ilike(f"%{fabric}%"))
        if product_type:
            base = base.where(Product.product_type == product_type)

        product_ids = base.scalar_subquery()

        colors_r = await self.db.execute(
            select(distinct(ProductVariant.color))
            .where(ProductVariant.product_id.in_(product_ids))
            .order_by(ProductVariant.color)
        )
        colors = [r for r in colors_r.scalars().all() if r]

        sizes_r = await self.db.execute(
            select(distinct(ProductVariant.size))
            .where(ProductVariant.product_id.in_(product_ids))
            .order_by(ProductVariant.size)
        )
        sizes = [r for r in sizes_r.scalars().all() if r]

        fabrics_r = await self.db.execute(
            select(distinct(Product.fabric))
            .where(Product.id.in_(product_ids))
            .order_by(Product.fabric)
        )
        fabrics = [r for r in fabrics_r.scalars().all() if r]

        types_r = await self.db.execute(
            select(distinct(Product.product_type))
            .where(Product.id.in_(product_ids))
            .order_by(Product.product_type)
        )
        product_types = [r for r in types_r.scalars().all() if r]

        price_r = await self.db.execute(
            select(func.min(Product.base_price), func.max(Product.base_price))
            .where(Product.id.in_(product_ids))
        )
        price_min, price_max = price_r.one()

        stores_r = await self.db.execute(
            select(Product.store_id, Store.name)
            .join(Store, Store.id == Product.store_id)
            .where(Product.id.in_(product_ids))
            .distinct()
            .order_by(Store.name)
        )
        stores = [{"id": row[0], "name": row[1]} for row in stores_r.all()]

        return {
            "colors": colors,
            "sizes": sizes,
            "fabrics": fabrics,
            "product_types": product_types,
            "price_range": {"min": float(price_min), "max": float(price_max)} if price_min is not None else None,
            "stores": stores,
        }

    async def get_with_details(self, product_id: str) -> Product | None:
        result = await self.db.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.images),
                selectinload(Product.variants),
                selectinload(Product.size_guides),
            )
        )
        return result.scalar_one_or_none()

    async def get_avg_rating(self, product_id: str) -> tuple[float | None, int]:
        result = await self.db.execute(
            select(func.avg(Review.rating), func.count(Review.id)).where(Review.product_id == product_id)
        )
        avg, count = result.one()
        return avg, count or 0

    async def is_wishlisted(self, user_id: str, product_id: str) -> bool:
        result = await self.db.execute(
            select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_variant(self, variant_id: str) -> ProductVariant | None:
        result = await self.db.execute(
            select(ProductVariant)
            .where(ProductVariant.id == variant_id)
            .options(selectinload(ProductVariant.product).selectinload(Product.images))
        )
        return result.scalar_one_or_none()

    async def get_size_guides(self, product_id: str) -> list[SizeGuide]:
        result = await self.db.execute(
            select(SizeGuide).where(SizeGuide.product_id == product_id)
        )
        return result.scalars().all()
