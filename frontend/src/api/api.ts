import type { Detection, Stats, HealthStatus, LogEntry, DispatchItem } from '@/data/types';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

let detectionIdCounter = 0;

function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  if (value < 0) return 0;
  if (value > 1) return 1;
  return value;
}

function mapBackendDetection(det: Record<string, unknown>, frameNumber: number): Detection {
  const bbox = det.bbox as number[];
  const origW = (det._orig_w as number) || 640;
  const origH = (det._orig_h as number) || 480;
  const x1 = (bbox?.[0] ?? 0) / origW;
  const y1 = (bbox?.[1] ?? 0) / origH;
  const x2 = (bbox?.[2] ?? 0) / origW;
  const y2 = (bbox?.[3] ?? 0) / origH;
  const nx1 = clamp01(Math.min(x1, x2));
  const ny1 = clamp01(Math.min(y1, y2));
  const nx2 = clamp01(Math.max(x1, x2));
  const ny2 = clamp01(Math.max(y1, y2));

  return {
    id: `#${(++detectionIdCounter).toString(16).toUpperCase().padStart(4, '0')}`,
    className: (det.label as string) || 'unknown',
    confidence: (det.confidence as number) || 0,
    hazardous: (det.hazardous as boolean) || false,
    recyclingBin: (det.recycling_bin as string) || 'E-Waste',
    bbox: {
      x: nx1,
      y: ny1,
      w: clamp01(nx2 - nx1),
      h: clamp01(ny2 - ny1),
    },
    timestamp: new Date().toLocaleTimeString('en-GB', { hour12: false }),
    frameNumber,
  };
}

function mapBackendStats(raw: Record<string, unknown>): Stats {
  const classDist = raw.top_detected_classes as [string, number][] | undefined;
  const totalDet = (raw.total_detections as number) || 0;

  return {
    totalFrames: (raw.total_frames_processed as number) || 0,
    totalDetections: totalDet,
    hazardousCount: (raw.total_hazardous_items as number) || 0,
    hazardRate: Math.round(((raw.hazard_rate as number) || 0) * 1000) / 10,
    classDistribution: (classDist || []).map(([name, count]) => ({
      name,
      count,
      percentage: totalDet > 0 ? Math.round((count / totalDet) * 100) : 0,
    })),
    recentTrend: (raw.recent_trend as number[]) || [],
  };
}

function mapBackendHealth(raw: Record<string, unknown>): HealthStatus {
  const deps = (raw.dependencies as Record<string, string>) || {};
  const tracking = (raw.tracking_stats as Record<string, number>) || {};
  const modelLoaded = deps.model === 'loaded';

  return {
    systemOnline: raw.status === 'healthy',
    tritonStatus: modelLoaded ? 'active' : 'offline',
    modelStatus: modelLoaded ? 'active' : 'offline',
    gpuLoad: (raw.gpu_load as number) ?? 0,
    memoryUsage: (raw.memory_usage as number) ?? 0,
    latencyMs: (raw.latency_ms as number) ?? 0,
    framesProcessed: tracking.total_frames || 0,
  };
}

function mapBackendLog(raw: Record<string, unknown>): LogEntry {
  return {
    timestamp: (raw.timestamp as string) || new Date().toLocaleTimeString('en-GB', { hour12: false }),
    level: (raw.level as LogEntry['level']) || 'system',
    message: (raw.message as string) || '',
  };
}

function mapBackendDispatch(raw: Record<string, unknown>): DispatchItem {
  return {
    id: (raw.id as string) || `batch-${Date.now()}`,
    batchName: (raw.batchName as string) || 'BATCH',
    status: (raw.status as DispatchItem['status']) || 'queued',
    progress: (raw.progress as number) || 0,
    icon: (raw.icon as string) || 'schedule',
  };
}

export async function fetchDetections(imageBlob?: Blob): Promise<Detection[]> {
  if (!imageBlob) return [];

  const formData = new FormData();
  formData.append('file', imageBlob, 'frame.jpg');

  const res = await fetch(`${API_BASE}/detect`, { method: 'POST', body: formData });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Detection API error ${res.status}: ${text || 'no response body'}`);
  }

  const data = await res.json();
  const detections = (data.detections || []) as Record<string, unknown>[];
  const frameNumber = (data.frame_number as number) || 0;
  return detections.map((d) => mapBackendDetection(d, frameNumber));
}

export async function fetchStats(): Promise<Stats> {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) throw new Error(`Stats API error: ${res.status}`);
    const raw = await res.json();
    return mapBackendStats(raw);
  } catch (err) {
    console.warn('[stats] Backend unreachable:', err);
    return {
      totalFrames: 0,
      totalDetections: 0,
      hazardousCount: 0,
      hazardRate: 0,
      classDistribution: [],
      recentTrend: [],
    };
  }
}

export async function fetchHealth(): Promise<HealthStatus> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const raw = await res.json();
    return mapBackendHealth(raw);
  } catch {
    return {
      systemOnline: false,
      tritonStatus: 'offline',
      modelStatus: 'offline',
      gpuLoad: 0,
      memoryUsage: 0,
      latencyMs: 0,
      framesProcessed: 0,
    };
  }
}

export async function fetchLogs(): Promise<LogEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/logs`);
    if (!res.ok) throw new Error(`Logs API error: ${res.status}`);
    const raw = await res.json();
    return (raw as Record<string, unknown>[]).map(mapBackendLog);
  } catch (err) {
    console.warn('[logs] Backend unreachable:', err);
    return [];
  }
}

export async function fetchDispatchQueue(): Promise<DispatchItem[]> {
  try {
    const res = await fetch(`${API_BASE}/dispatch`);
    if (!res.ok) throw new Error(`Dispatch API error: ${res.status}`);
    const raw = await res.json();
    return (raw as Record<string, unknown>[]).map(mapBackendDispatch);
  } catch (err) {
    console.warn('[dispatch] Backend unreachable:', err);
    return [];
  }
}

export async function resetTracking(): Promise<void> {
  try {
    await fetch(`${API_BASE}/track/reset`, { method: 'POST' });
  } catch {
    // silent
  }
  detectionIdCounter = 0;
}
