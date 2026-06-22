from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.order import Order, OrderItem, OrderStore, OrderStatus
from app.models.user import User
from app.repositories.cart_repo import CartRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.order import OrderCreate, OrderResponse


DELIVERY_FEE_PER_STORE = 2000.0


class OrderService:
    def __init__(self, db: AsyncSession):
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)

    async def create_from_cart(self, user: User, data: OrderCreate) -> OrderResponse:
        cart = await self.cart_repo.get_by_user(user.id)
        if not cart or not cart.items:
            raise BadRequestError("Cart is empty")

        items_by_store: dict[str, list] = {}
        for item in cart.items:
            v = item.variant
            if not v.is_available or v.stock_quantity < item.quantity:
                raise BadRequestError(f"'{v.product.name}' is no longer available in the requested quantity")
            items_by_store.setdefault(v.product.store_id, []).append(item)

        total = 0.0
        order = Order(user_id=user.id, address_id=data.address_id, notes=data.notes, total_amount=0)
        self.order_repo.db.add(order)
        await self.order_repo.db.flush()

        for store_id, store_items in items_by_store.items():
            subtotal = sum(
                float(i.variant.price_override or i.variant.product.base_price) * i.quantity
                for i in store_items
            )
            order_store = OrderStore(
                order_id=order.id,
                store_id=store_id,
                delivery_fee=DELIVERY_FEE_PER_STORE,
                subtotal=subtotal,
            )
            self.order_repo.db.add(order_store)
            await self.order_repo.db.flush()

            for item in store_items:
                v = item.variant
                self.order_repo.db.add(OrderItem(
                    order_store_id=order_store.id,
                    product_variant_id=v.id,
                    product_name=v.product.name,
                    color=v.color,
                    size=v.size,
                    unit_price=float(v.price_override or v.product.base_price),
                    quantity=item.quantity,
                ))
                v.stock_quantity -= item.quantity

            total += subtotal + DELIVERY_FEE_PER_STORE

        order.total_amount = total
        for item in cart.items:
            await self.order_repo.db.delete(item)

        await self.order_repo.db.commit()
        return await self.get_order(user, order.id)

    async def get_order(self, user: User, order_id: str) -> OrderResponse:
        order = await self.order_repo.get_with_details(order_id)
        if not order:
            raise NotFoundError("Order not found")
        if order.user_id != user.id:
            raise ForbiddenError()
        return self._to_response(order)

    async def cancel_order_store(self, user: User, order_store_id: str) -> dict:
        order_store = await self.order_repo.get_order_store(order_store_id)
        if not order_store:
            raise NotFoundError("Order not found")
        order = await self.order_repo.get_by_id(order_store.order_id)
        if order.user_id != user.id:
            raise ForbiddenError()
        if order_store.status not in (OrderStatus.pending, OrderStatus.accepted):
            raise BadRequestError("Order cannot be cancelled at this stage")
        order_store.status = OrderStatus.cancelled
        await self.order_repo.db.commit()
        return {"message": "Order cancelled"}

    def _to_response(self, order: Order) -> OrderResponse:
        from app.schemas.order import AddressResponse, OrderItemResponse, OrderListItem, OrderStoreResponse
        return OrderResponse(
            id=order.id,
            total_amount=float(order.total_amount),
            notes=order.notes,
            address=AddressResponse.model_validate(order.address),
            store_orders=[
                OrderStoreResponse(
                    id=os.id,
                    store_id=os.store_id,
                    store_name=os.store.name,
                    status=os.status,
                    delivery_fee=float(os.delivery_fee),
                    subtotal=float(os.subtotal),
                    items=[
                        OrderItemResponse(
                            id=i.id,
                            product_id=i.variant.product_id if i.variant else None,
                            product_name=i.product_name,
                            color=i.color,
                            size=i.size,
                            unit_price=float(i.unit_price),
                            quantity=i.quantity,
                        )
                        for i in os.items
                    ],
                )
                for os in order.store_orders
            ],
            created_at=order.created_at.isoformat(),
        )
