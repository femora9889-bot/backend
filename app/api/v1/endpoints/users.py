from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.infrastructure.storage.cloudinary_client import upload_image
from app.models.user import User
from app.schemas.user import MeasurementsCreate, MeasurementsResponse, UserProfileUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await UserService(db).get_profile(user)


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UserService(db).update_profile(user, data)


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    url = await upload_image(content, "profile", public_id=f"user_{user.id}")
    return await UserService(db).update_profile_image(user, url)


@router.put("/me/measurements", response_model=MeasurementsResponse)
async def save_measurements(
    data: MeasurementsCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UserService(db).save_measurements(user, data)


@router.get("/me/measurements", response_model=MeasurementsResponse)
async def get_measurements(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await UserService(db).get_measurements(user)
