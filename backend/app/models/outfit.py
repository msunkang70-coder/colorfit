from sqlalchemy import String, Integer, Boolean, SmallInteger, Text, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Outfit(Base):
    __tablename__ = "outfits"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    item_ids: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    gender: Mapped[str | None] = mapped_column(String(10), index=True)
    designed_tpo: Mapped[str | None] = mapped_column(String(20), index=True)
    designed_moods: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    total_price: Mapped[int | None] = mapped_column(Integer)
    lowest_total_price: Mapped[int | None] = mapped_column(Integer)
    is_complete_outfit: Mapped[bool | None] = mapped_column(Boolean)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    scores: Mapped[dict | None] = mapped_column(JSONB)
    style_details: Mapped[dict | None] = mapped_column(JSONB)
    reasons: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    llm_quality_score: Mapped[int | None] = mapped_column(SmallInteger)
