// En browser usa el mismo host, en SSR fallback a localhost
const BASE = typeof window !== "undefined"
  ? `http://${window.location.hostname}:8000`
  : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");
const TIMEOUT_MS = 3000;

export function getApiBase(): string {
  return typeof window !== "undefined"
    ? `http://${window.location.hostname}:8000`
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");
}

export function getStageImageUrl(artworkId: string, stageNumber: number): string {
  // Return full API endpoint - images are served from backend via stages endpoint
  return `${getApiBase()}/api/stages/${artworkId}/${stageNumber}/image`;
}

async function fetchWithTimeout(url: string, options?: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

async function get<T>(path: string): Promise<T> {
  const res = await fetchWithTimeout(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetchWithTimeout(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetchWithTimeout(`${BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`PATCH ${path} → ${res.status}`);
  return res.json();
}

// ── Artworks ──────────────────────────────────────────
export async function fetchArtworks() {
  return get<unknown[]>("/api/artworks");
}

export async function fetchArtwork(id: string) {
  return get<unknown>(`/api/artworks/${id}`);
}

// ── Sessions ──────────────────────────────────────────
export async function createSession(artworkId: string, startStage: number, totalStages: number) {
  return post<{ id: string }>("/api/sessions", {
    artwork_id: artworkId,
    start_stage: startStage,
    total_stages: totalStages,
  });
}

export async function advanceStage(sessionId: string, stage: number) {
  return patch(`/api/sessions/${sessionId}/stage`, { stage });
}

export async function recordMetric(sessionId: string, data: {
  stage: number;
  precision_pct: number;
  color_deviation: number;
  elapsed_s: number;
  feedback_json?: object;
}) {
  return post(`/api/sessions/${sessionId}/metrics`, data);
}

// ── Hardware ──────────────────────────────────────────
export async function apiDispense(slot = 1, duration_ms = 500) {
  return post("/api/hardware/dispense", { pigment_slot: slot, duration_ms });
}

export async function apiClean() {
  return post("/api/hardware/clean", {});
}

export async function fetchHardwareStatus() {
  return get("/api/hardware/status");
}

// ── Stages ────────────────────────────────────────────
export async function fetchStages(artworkId: string) {
  return get<unknown[]>(`/api/stages/${artworkId}`);
}

export async function projectStage(artworkId: string, stageNumber: number): Promise<void> {
  try {
    await post(`/api/stages/${artworkId}/${stageNumber}/project`, {});
  } catch (e) {
    console.warn("Projection command failed:", e);
  }
}

// ── Health ────────────────────────────────────────────
export async function checkHealth(): Promise<boolean> {
  try {
    await get("/health");
    return true;
  } catch {
    return false;
  }
}
