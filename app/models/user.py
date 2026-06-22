import enum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, uuid_pk


class UserRole(str, enum.Enum):
    customer = "customer"
    merchant = "merchant"
    admin = "admin"


class BodyShape(str, enum.Enum):
    pear = "pear"
    apple = "apple"
    hourglass = "hourglass"
    rectangle = "rectangle"
    inverted_triangle = "inverted_triangle"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    profile_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.customer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    measurements: Mapped["UserMeasurements | None"] = relationship(back_populates="user", uselist=False)
    addresses: Mapped[list["Address"]] = relationship(back_populates="user")
    cart: Mapped["Cart | None"] = relationship(back_populates="user", uselist=False)
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user")
    wishlist_items: Mapped[list["Wishlist"]] = relationship(back_populates="user")
    store_wishlist_items: Mapped[list["StoreWishlist"]] = relationship(back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
    tryon_sessions: Mapped[list["TryOnSession"]] = relationship(back_populates="user")


class UserMeasurements(Base):
    __tablename__ = "user_measurements"

    id: Mapped[str] = uuid_pk()
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    body_shape: Mapped[BodyShape] = mapped_column(Enum(BodyShape))
    bust_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hips_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    shoulder_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_arm_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    thigh_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    calf_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    torso_length_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    secondary_shape: Mapped[BodyShape | None] = mapped_column(Enum(BodyShape), nullable=True)
    skin_tone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hair_color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user: Mapped["User"] = relationship(back_populates="measurements")


from app.models.address import Address
from app.models.cart import Cart
from app.models.notification import Notification
from app.models.order import Order
from app.models.review import Review
from app.models.tryon import TryOnSession
from app.models.wishlist import StoreWishlist, Wishlist
