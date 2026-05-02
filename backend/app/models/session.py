from sqlalchemy import String, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
import time


class Session(Base):
    __tablename__ = "sessions"

    id:            Mapped[str] = mapped_column(String, primary_key=True)
    artwork_id:    Mapped[str] = mapped_column(String, nullable=False)
    current_stage: Mapped[int] = mapped_column(Integer, default=1)
    total_stages:  Mapped[int] = mapped_column(Integer, nullable=False)
    started_at:    Mapped[float] = mapped_column(Float, default=time.time)
    ended_at:      Mapped[float | None] = mapped_column(Float, nullable=True)
    status:        Mapped[str] = mapped_column(String, default="active")  # active | completed | aborted


class SessionMetric(Base):
    __tablename__ = "session_metrics"

    id:            Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id:    Mapped[str] = mapped_column(String, nullable=False)
    stage:         Mapped[int] = mapped_column(Integer, nullable=False)
    precision_pct: Mapped[float] = mapped_column(Float, nullable=False)
    color_deviation: Mapped[float] = mapped_column(Float, nullable=False)
    elapsed_s:     Mapped[float] = mapped_column(Float, nullable=False)
    feedback_json: Mapped[dict] = mapped_column(JSON, default=dict)
    recorded_at:   Mapped[float] = mapped_column(Float, default=time.time)
