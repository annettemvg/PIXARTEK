"""JSON payload schemas (dataclasses) for all MQTT messages."""
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class ProjectionCommand:
    artwork_id: str
    stage: int
    image_path: str
    total_stages: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class ProjectionStatus:
    artwork_id: str
    stage: int
    active: bool
    node: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class VisionFeedback:
    artwork_id: str
    stage: int
    precision_pct: float          # 0–100
    stroke_errors: list[str]
    color_deviation: float        # delta-E units
    suggestions: list[str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class VisionMetrics:
    session_id: str
    stage: int
    precision_pct: float
    elapsed_s: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class Heartbeat:
    node: str
    status: str                   # "ok" | "degraded" | "error"
    timestamp: float = field(default_factory=time.time)
