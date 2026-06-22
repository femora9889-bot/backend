from sqlalchemy import Boolean, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, uuid_pk


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[str] = uuid_pk()
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_price: Mapped[float] = mapped_column(Numeric(10, 2))
    fabric: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    store: Mapped["Store"] = relationship(back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(back_populates="product", order_by="ProductImage.display_order")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product")
    size_guides: Mapped[list["SizeGuide"]] = relationship(back_populates="product")
    reviews: Mapped[list["Review"]] = relationship(back_populates="product")
    wishlist_items: Mapped[list["Wishlist"]] = relationship(back_populates="product")
    tryon_sessions: Mapped[list["TryOnSession"]] = relationship(back_populates="product")


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[str] = uuid_pk()
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    url: Mapped[str] = mapped_column(String(500))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped["Product"] = relationship(back_populates="images")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[str] = uuid_pk()
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    color: Mapped[str] = mapped_column(String(50))
    color_hex: Mapped[str | None] = mapped_column(String(7), nullable=True)
    size: Mapped[str] = mapped_column(String(20))
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    original_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_override: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    product: Mapped["Product"] = relationship(back_populates="variants")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="variant")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="variant")


class SizeGuide(Base):
    __tablename__ = "size_guides"

    id: Mapped[str] = uuid_pk()
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    size_label: Mapped[str] = mapped_column(String(20))
    bust_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hips_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    length_cm: Mapped[float | None] = mapped_column(Float, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="size_guides")


from app.models.cart import CartItem
from app.models.order import OrderItem
from app.models.review import Review
from app.models.store import Store
from app.models.tryon import TryOnSession
from app.models.wishlist import Wishlist
