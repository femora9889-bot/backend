from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, uuid_pk


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    name_ar: Mapped[str] = mapped_column(String(100))

    store_links: Mapped[list["StoreCategory"]] = relationship(back_populates="category")


class Store(Base, TimestampMixin):
    __tablename__ = "stores"

    id: Mapped[str] = uuid_pk()
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200), index=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(300))
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone: Mapped[str] = mapped_column(String(20))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category_links: Mapped[list["StoreCategory"]] = relationship(back_populates="store")
    products: Mapped[list["Product"]] = relationship(back_populates="store")
    order_stores: Mapped[list["OrderStore"]] = relationship(back_populates="store")
    wishlist_items: Mapped[list["StoreWishlist"]] = relationship(back_populates="store")


class StoreCategory(Base):
    __tablename__ = "store_categories"

    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), primary_key=True)

    store: Mapped["Store"] = relationship(back_populates="category_links")
    category: Mapped["Category"] = relationship(back_populates="store_links")


from app.models.order import OrderStore
from app.models.product import Product
from app.models.wishlist import StoreWishlist
