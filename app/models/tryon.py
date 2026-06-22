from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import uuid_pk


class TryOnSession(Base):
    __tablename__ = "tryon_sessions"

    id: Mapped[str] = uuid_pk()
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    input_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fit_assessment: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="tryon_sessions")
    product: Mapped["Product"] = relationship(back_populates="tryon_sessions")


from app.models.product import Product
from app.models.user import User
