export interface Detection {
  readonly id: string;
  readonly className: string;
  readonly confidence: number;
  readonly hazardous: boolean;
  readonly recyclingBin: string;
  readonly bbox: { x: number; y: number; w: number; h: number };
  readonly timestamp: string;
  readonly frameNumber: number;
}

export interface Stats {
  readonly totalFrames: number;
  readonly totalDetections: number;
  readonly hazardousCount: number;
  readonly hazardRate: number;
  readonly classDistribution: readonly { name: string; count: number; percentage: number }[];
  readonly recentTrend: readonly number[];
}

export interface HealthStatus {
  readonly systemOnline: boolean;
  readonly tritonStatus: 'active' | 'degraded' | 'offline';
  readonly modelStatus: 'active' | 'degraded' | 'offline';
  readonly gpuLoad: number;
  readonly memoryUsage: number;
  readonly latencyMs: number;
  readonly framesProcessed: number;
}

export interface LogEntry {
  readonly timestamp: string;
  readonly level: 'info' | 'warning' | 'danger' | 'system';
  readonly message: string;
}

export interface DispatchItem {
  readonly id: string;
  readonly batchName: string;
  readonly status: 'ready' | 'sorting' | 'queued' | 'dispatched';
  readonly progress: number;
  readonly icon: string;
}
