export type NodeId = "rpi5-main" | "rpi4-projection" | "rpi4-vision";
export type NodeState = "ok" | "degraded" | "error" | "offline";

export interface NodeStatus {
  id: NodeId;
  label: string;
  state: NodeState;
  lastSeen: number; // timestamp
}

export interface StrokeError {
  zone: string;
  message: string;
}

export interface VisionFeedback {
  precision_pct: number;        // 0–100
  color_deviation: number;      // delta-E, lower is better
  stroke_errors: StrokeError[];
  suggestions: string[];
  timestamp: number;
}

export interface StageMetric {
  stage: number;
  precision_pct: number;
  color_deviation: number;
  elapsed_s: number;
}

export interface SessionState {
  artworkId: string;
  currentStage: number;
  totalStages: number;
  startedAt: number;
  elapsed_s: number;
  feedback: VisionFeedback | null;
  nodes: NodeStatus[];
  projectionActive: boolean;
  dispensing: boolean;
  cleaning: boolean;
  completed: boolean;
  stageMetrics: StageMetric[];
}

export interface UserProfile {
  id: string;
  name: string;
  avatar: string; // emoji
}
