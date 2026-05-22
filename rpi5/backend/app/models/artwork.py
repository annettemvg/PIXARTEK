from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Artwork(Base):
    __tablename__ = "artworks"

    id:           Mapped[str] = mapped_column(String, primary_key=True)
    title:        Mapped[str] = mapped_column(String, nullable=False)
    artist:       Mapped[str] = mapped_column(String, nullable=False)
    year:         Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty:   Mapped[str] = mapped_column(String, nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    color:        Mapped[str] = mapped_column(String, nullable=False)
    image:        Mapped[str] = mapped_column(String, nullable=False)
    tags:         Mapped[list] = mapped_column(JSON, default=list)
    stages:       Mapped[list] = mapped_column(JSON, default=list)
