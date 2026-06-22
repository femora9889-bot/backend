from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import uuid_pk
from datetime import datetime, timezone
from sqlalchemy import DateTime


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("user_id", "product_id", "order_store_id"),)

    id: Mapped[str] = uuid_pk()
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    order_store_id: Mapped[str] = mapped_column(ForeignKey("order_stores.id"))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="reviews")
    product: Mapped["Product"] = relationship(back_populates="reviews")
    order_store: Mapped["OrderStore"] = relationship(back_populates="reviews")
    helpful_marks: Mapped[list["ReviewHelpful"]] = relationship(back_populates="review", cascade="all, delete-orphan")


class ReviewHelpful(Base):
    __tablename__ = "review_helpfuls"
    __table_args__ = (UniqueConstraint("review_id", "user_id"),)

    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)

    review: Mapped["Review"] = relationship(back_populates="helpful_marks")


from app.models.order import OrderStore
from app.models.product import Product
from app.models.user import User
