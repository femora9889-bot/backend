from pydantic import BaseModel

from app.models.order import OrderStatus


class AddressCreate(BaseModel):
    label: str
    city: str
    area: str
    street: str | None = None
    building: str | None = None
    notes: str | None = None
    is_default: bool = False


class AddressResponse(BaseModel):
    id: str
    label: str
    city: str
    area: str
    street: str | None
    building: str | None
    notes: str | None
    is_default: bool

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    address_id: str
    notes: str | None = None


class OrderItemResponse(BaseModel):
    id: str
    product_id: str | None = None
    product_name: str
    color: str
    size: str
    unit_price: float
    quantity: int

    model_config = {"from_attributes": True}


class OrderStoreResponse(BaseModel):
    id: str
    store_id: str
    store_name: str
    status: OrderStatus
    delivery_fee: float
    subtotal: float
    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: str
    total_amount: float
    notes: str | None
    address: AddressResponse
    store_orders: list[OrderStoreResponse] = []
    created_at: str

    model_config = {"from_attributes": True}


class OrderListItem(BaseModel):
    id: str
    total_amount: float
    status_summary: str
    store_count: int
    created_at: str

    model_config = {"from_attributes": True}
