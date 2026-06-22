from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.cart import Cart, CartItem
from app.models.user import User
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartItemResponse, CartResponse


class CartService:
    def __init__(self, db: AsyncSession):
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)

    async def _get_or_create_cart(self, user: User) -> Cart:
        cart = await self.cart_repo.get_by_user(user.id)
        if not cart:
            cart = Cart(user_id=user.id)
            await self.cart_repo.save(cart)
        return cart

    async def get_cart(self, user: User) -> CartResponse:
        cart = await self.cart_repo.get_by_user(user.id)
        if not cart or not cart.items:
            return CartResponse()
        return self._build_response(cart.items)

    async def add_item(self, user: User, data: CartItemAdd) -> CartResponse:
        variant = await self.product_repo.get_variant(data.product_variant_id)
        if not variant or not variant.is_available:
            raise NotFoundError("Product variant not found or unavailable")
        if variant.stock_quantity < data.quantity:
            raise BadRequestError(f"Only {variant.stock_quantity} items available in stock")

        cart = await self._get_or_create_cart(user)
        existing = await self.cart_repo.get_item(cart.id, data.product_variant_id)

        if existing:
            new_qty = existing.quantity + data.quantity
            if new_qty > variant.stock_quantity:
                raise BadRequestError(f"Cannot add more than {variant.stock_quantity} items")
            existing.quantity = new_qty
            await self.cart_repo.save(existing)
        else:
            item = CartItem(cart_id=cart.id, product_variant_id=data.product_variant_id, quantity=data.quantity)
            self.cart_repo.db.add(item)
            await self.cart_repo.db.commit()

        return await self.get_cart(user)

    async def update_item(self, user: User, variant_id: str, data: CartItemUpdate) -> CartResponse:
        cart = await self.cart_repo.get_by_user(user.id)
        if not cart:
            raise NotFoundError("Cart not found")

        item = await self.cart_repo.get_item(cart.id, variant_id)
        if not item:
            raise NotFoundError("Item not in cart")

        if data.quantity <= 0:
            await self.cart_repo.delete(item)
        else:
            variant = await self.product_repo.get_variant(variant_id)
            if data.quantity > variant.stock_quantity:
                raise BadRequestError(f"Only {variant.stock_quantity} available")
            item.quantity = data.quantity
            await self.cart_repo.save(item)

        return await self.get_cart(user)

    async def remove_item(self, user: User, variant_id: str) -> CartResponse:
        cart = await self.cart_repo.get_by_user(user.id)
        if not cart:
            raise NotFoundError("Cart not found")
        item = await self.cart_repo.get_item(cart.id, variant_id)
        if item:
            await self.cart_repo.delete(item)
        return await self.get_cart(user)

    def _build_response(self, items: list[CartItem]) -> CartResponse:
        by_store: dict[str, list[CartItemResponse]] = {}
        total = 0.0

        for item in items:
            v = item.variant
            product = v.product
            price = float(v.price_override or product.base_price)
            store_id = product.store_id
            primary_img = next((img.url for img in product.images if img.is_primary), None)

            cart_item = CartItemResponse(
                id=item.id,
                product_variant_id=v.id,
                product_name=product.name,
                color=v.color,
                size=v.size,
                price=price,
                original_price=float(v.original_price) if v.original_price else None,
                image_url=primary_img,
                store_id=store_id,
                store_name=product.store.name if hasattr(product, "store") else "",
                quantity=item.quantity,
                stock_quantity=v.stock_quantity,
            )
            by_store.setdefault(store_id, []).append(cart_item)
            total += price * item.quantity

        return CartResponse(items_by_store=by_store, total=round(total, 2))
