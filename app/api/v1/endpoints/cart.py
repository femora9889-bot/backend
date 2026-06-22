from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartResponse)
async def get_cart(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await CartService(db).get_cart(user)


@router.post("/items", response_model=CartResponse, status_code=201)
async def add_item(data: CartItemAdd, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await CartService(db).add_item(user, data)


@router.patch("/items/{variant_id}", response_model=CartResponse)
async def update_item(
    variant_id: str,
    data: CartItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CartService(db).update_item(user, variant_id, data)


@router.delete("/items/{variant_id}", response_model=CartResponse)
async def remove_item(
    variant_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CartService(db).remove_item(user, variant_id)
