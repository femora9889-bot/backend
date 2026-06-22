from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStore
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)

    async def get_user_orders(self, user_id: str, offset: int = 0, limit: int = 20) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.store_orders))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_with_details(self, order_id: str) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.address),
                selectinload(Order.store_orders).selectinload(OrderStore.items).selectinload(OrderItem.variant),
                selectinload(Order.store_orders).selectinload(OrderStore.store),
            )
        )
        return result.scalar_one_or_none()

    async def get_order_store(self, order_store_id: str) -> OrderStore | None:
        result = await self.db.execute(
            select(OrderStore).where(OrderStore.id == order_store_id)
        )
        return result.scalar_one_or_none()
