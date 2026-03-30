from datetime import datetime

from sqlalchemy import String, Integer, Text, SmallInteger, ARRAY, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(20))
    color_hex: Mapped[str | None] = mapped_column(String(7))
    tone_id: Mapped[str | None] = mapped_column(String(30), index=True)
    price: Mapped[int | None] = mapped_column(Integer)
    mall_name: Mapped[str | None] = mapped_column(String(50))
    mall_url: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    gender: Mapped[str | None] = mapped_column(String(10), index=True)
    silhouette: Mapped[str | None] = mapped_column(String(20))
    formality: Mapped[int | None] = mapped_column(SmallInteger)
    last_observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
