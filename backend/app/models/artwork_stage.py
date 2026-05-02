from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
import uuid, datetime


class ArtworkStage(Base):
    __tablename__ = "artwork_stages"

    stage_id:              Mapped[str]      = mapped_column(String,  primary_key=True, default=lambda: str(uuid.uuid4()))
    artwork_id:            Mapped[str]      = mapped_column(String,  nullable=False, index=True)
    stage_number:          Mapped[int]      = mapped_column(Integer, nullable=False)
    image_path:            Mapped[str]      = mapped_column(Text,    nullable=False)
    projection_image_path: Mapped[str]      = mapped_column(Text,    nullable=False)
    created_at:            Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
