import uuid
from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    tone_preferences: Mapped[dict | None] = mapped_column(JSONB, default={})
    category_preferences: Mapped[dict | None] = mapped_column(JSONB, default={})
    brand_preferences: Mapped[dict | None] = mapped_column(JSONB, default={})
    avg_liked_price: Mapped[int | None] = mapped_column(Integer)
    feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    weight_overrides: Mapped[dict | None] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
