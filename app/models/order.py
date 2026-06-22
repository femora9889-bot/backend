import enum

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, uuid_pk


class OrderStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    preparing = "preparing"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[str] = uuid_pk()
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    address_id: Mapped[str] = mapped_column(ForeignKey("addresses.id"))
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="orders")
    address: Mapped["Address"] = relationship()
    store_orders: Mapped[list["OrderStore"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderStore(Base, TimestampMixin):
    __tablename__ = "order_stores"

    id: Mapped[str] = uuid_pk()
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending)
    delivery_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2))
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship(back_populates="store_orders")
    store: Mapped["Store"] = relationship(back_populates="order_stores")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order_store", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="order_store")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = uuid_pk()
    order_store_id: Mapped[str] = mapped_column(ForeignKey("order_stores.id"))
    product_variant_id: Mapped[str] = mapped_column(ForeignKey("product_variants.id"))
    product_name: Mapped[str] = mapped_column(String(200))
    color: Mapped[str] = mapped_column(String(50))
    size: Mapped[str] = mapped_column(String(20))
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer)

    order_store: Mapped["OrderStore"] = relationship(back_populates="items")
    variant: Mapped["ProductVariant"] = relationship(back_populates="order_items")


from app.models.address import Address
from app.models.product import ProductVariant
from app.models.review import Review
from app.models.store import Store
from app.models.user import User
