from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User, UserMeasurements
from app.repositories.user_repo import MeasurementsRepository, UserRepository
from app.schemas.user import MeasurementsCreate, MeasurementsResponse, UserProfileUpdate, UserResponse
from app.services.fit_service import classify_torso, detect_body_shape


class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.measurements_repo = MeasurementsRepository(db)

    async def get_profile(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    async def update_profile(self, user: User, data: UserProfileUpdate) -> UserResponse:
        if data.phone and data.phone != user.phone:
            existing = await self.user_repo.get_by_phone(data.phone)
            if existing:
                raise ConflictError("Phone number already in use")
            user.phone = data.phone
        if data.name:
            user.name = data.name
        await self.user_repo.save(user)
        return UserResponse.model_validate(user)

    async def update_profile_image(self, user: User, image_url: str) -> UserResponse:
        user.profile_image = image_url
        await self.user_repo.save(user)
        return UserResponse.model_validate(user)

    async def save_measurements(self, user: User, data: MeasurementsCreate) -> MeasurementsResponse:
        shape_profile = None
        if data.bust_cm and data.waist_cm and data.hips_cm:
            shape_profile = detect_body_shape(data.bust_cm, data.waist_cm, data.hips_cm)

        existing = await self.measurements_repo.get_by_user(user.id)
        if existing:
            for field, value in data.model_dump(exclude_none=True).items():
                setattr(existing, field, value)
            if shape_profile:
                existing.body_shape = shape_profile.primary
                existing.secondary_shape = shape_profile.secondary
            await self.measurements_repo.save(existing)
            return MeasurementsResponse.model_validate(existing)

        measurements = UserMeasurements(
            user_id=user.id,
            body_shape=shape_profile.primary if shape_profile else None,
            secondary_shape=shape_profile.secondary if shape_profile else None,
            **data.model_dump(),
        )
        await self.measurements_repo.save(measurements)
        return MeasurementsResponse.model_validate(measurements)

    async def get_measurements(self, user: User) -> MeasurementsResponse:
        m = await self.measurements_repo.get_by_user(user.id)
        if not m:
            raise NotFoundError("Measurements not found")
        response = MeasurementsResponse.model_validate(m)
        if m.torso_length_cm and m.height_cm:
            torso_type, _ = classify_torso(m.torso_length_cm, m.height_cm)
            response.torso_type = torso_type
        return response
