import httpx
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.tryon import TryOnSession
from app.models.user import User
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import MeasurementsRepository
from app.schemas.tryon import FitResult, TryOnResponse
from app.services.fit_service import calculate_fit
from app.services.tryon_service import generate_avatar, tryon_on_avatar, tryon_with_photo

router = APIRouter(prefix="/tryon", tags=["Try-On"])


@router.get("/debug/models")
async def list_gemini_models():
    async with httpx.AsyncClient(timeout=15) as http:
        resp = await http.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            params={"key": settings.GEMINI_API_KEY, "pageSize": 100},
        )
    models = resp.json().get("models", [])
    image_models = [
        {"name": m["name"], "methods": m.get("supportedGenerationMethods", [])}
        for m in models
        if any("image" in m["name"].lower() or "imagen" in m["name"].lower()
               for _ in [1])
        or "generateContent" in m.get("supportedGenerationMethods", [])
    ]
    return {"total": len(models), "image_related": image_models}


@router.post("/avatar", summary="توليد Avatar من القياسات")
async def create_avatar(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    m_repo = MeasurementsRepository(db)
    measurements = await m_repo.get_by_user(user.id)
    if not measurements:
        raise BadRequestError("أضيفي قياساتك أولاً")

    avatar_url = await generate_avatar(measurements, user.id)

    measurements.avatar_url = avatar_url
    await m_repo.save(measurements)

    return {"avatar_url": avatar_url}


@router.post("/{product_id}", response_model=TryOnResponse)
async def try_on(
    product_id: str,
    selected_size: str = Query(...),
    photo: UploadFile | None = File(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product_repo = ProductRepository(db)
    product = await product_repo.get_with_details(product_id)
    if not product:
        raise NotFoundError("المنتج غير موجود")

    m_repo = MeasurementsRepository(db)
    measurements = await m_repo.get_by_user(user.id)
    if not measurements:
        raise BadRequestError("أضيفي قياساتك أولاً")

    fit = calculate_fit(measurements, product.size_guides, selected_size)

    primary_image = next((img.url for img in product.images if img.is_primary), None)
    if not primary_image:
        raise BadRequestError("المنتج ليس له صورة")

    if photo:
        photo_bytes = await photo.read()
        result_url = await tryon_with_photo(photo_bytes, primary_image, user.id)
    elif measurements.avatar_url:
        result_url = await tryon_on_avatar(measurements.avatar_url, primary_image, user.id)
    else:
        avatar_url = await generate_avatar(measurements, user.id)
        measurements.avatar_url = avatar_url
        await m_repo.save(measurements)
        result_url = await tryon_on_avatar(avatar_url, primary_image, user.id)

    session = TryOnSession(
        user_id=user.id,
        product_id=product_id,
        input_photo_url=result_url,
        result_url=result_url,
        fit_score=fit.score,
        fit_assessment=fit.assessment,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return TryOnResponse(
        session_id=session.id,
        result_url=result_url,
        fit=fit,
    )
