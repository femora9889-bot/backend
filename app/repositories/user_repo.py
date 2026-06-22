from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserMeasurements
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_with_measurements(self, user_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id).options(selectinload(User.measurements))
        )
        return result.scalar_one_or_none()


class MeasurementsRepository(BaseRepository[UserMeasurements]):
    def __init__(self, db: AsyncSession):
        super().__init__(UserMeasurements, db)

    async def get_by_user(self, user_id: str) -> UserMeasurements | None:
        result = await self.db.execute(
            select(UserMeasurements).where(UserMeasurements.user_id == user_id)
        )
        return result.scalar_one_or_none()
