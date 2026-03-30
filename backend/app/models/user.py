import uuid
from datetime import datetime

from sqlalchemy import String, Integer, ARRAY, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str | None] = mapped_column(String(20))
    gender: Mapped[str | None] = mapped_column(String(10), index=True)
    tone_id: Mapped[str | None] = mapped_column(String(30), index=True)
    tpo_primary: Mapped[str | None] = mapped_column(String(20))
    tpo_secondary: Mapped[str | None] = mapped_column(String(20))
    tpo_list: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    style_moods: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    budget_min: Mapped[int | None] = mapped_column(Integer)
    budget_max: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
