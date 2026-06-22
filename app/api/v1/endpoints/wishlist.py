from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.wishlist import StoreWishlistResponse, WishlistResponse
from app.services.wishlist_service import WishlistService

router = APIRouter(tags=["Wishlist"])


@router.get("/wishlist/products", response_model=WishlistResponse)
async def get_wishlist(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await WishlistService(db).get_products(user)


@router.post("/wishlist/products/{product_id}", response_model=WishlistResponse)
async def toggle_product(
    product_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WishlistService(db).toggle_product(user, product_id)


@router.get("/wishlist/stores", response_model=StoreWishlistResponse)
async def get_store_wishlist(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await WishlistService(db).get_stores(user)


@router.post("/wishlist/stores/{store_id}", response_model=StoreWishlistResponse)
async def toggle_store(
    store_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WishlistService(db).toggle_store(user, store_id)
