from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.order_repo import OrderRepository
from app.schemas.order import AddressCreate, AddressResponse, OrderCreate, OrderListItem, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(tags=["Orders"])


@router.post("/addresses", response_model=AddressResponse, status_code=201)
async def add_address(
    data: AddressCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, update
    from app.models.address import Address
    if data.is_default:
        await db.execute(
            update(Address).where(Address.user_id == user.id).values(is_default=False)
        )
    address = Address(user_id=user.id, **data.model_dump())
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return AddressResponse.model_validate(address)


@router.get("/addresses", response_model=list[AddressResponse])
async def get_addresses(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.address import Address
    result = await db.execute(select(Address).where(Address.user_id == user.id))
    return [AddressResponse.model_validate(a) for a in result.scalars().all()]


@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    data: OrderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await OrderService(db).create_from_cart(user, data)


@router.get("/orders", response_model=list[OrderListItem])
async def list_orders(
    page: int = Query(1, ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    orders = await OrderRepository(db).get_user_orders(user.id, offset=(page - 1) * 20)
    return [
        OrderListItem(
            id=o.id,
            total_amount=float(o.total_amount),
            status_summary=o.store_orders[0].status if o.store_orders else "pending",
            store_count=len(o.store_orders),
            created_at=o.created_at.isoformat(),
        )
        for o in orders
    ]


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await OrderService(db).get_order(user, order_id)


@router.post("/orders/stores/{order_store_id}/cancel")
async def cancel_order(
    order_store_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await OrderService(db).cancel_order_store(user, order_store_id)
