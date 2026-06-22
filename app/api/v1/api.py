from fastapi import APIRouter

from app.api.v1.endpoints import auth, cart, categories, orders, products, reviews, stores, tryon, users, wishlist

router = APIRouter()

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(categories.router)
router.include_router(stores.router)
router.include_router(reviews.router)
router.include_router(products.router)
router.include_router(cart.router)
router.include_router(orders.router)
router.include_router(wishlist.router)
router.include_router(tryon.router)
