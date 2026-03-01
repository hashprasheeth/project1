import { useState, useRef, useCallback, useEffect } from 'react';
import { fetchDetections } from '@/api/api';
import type { Detection } from '@/data/types';

export type VideoSource = 'none' | 'webcam' | 'upload';

interface DigitalTwinState {
  readonly isRunning: boolean;
  readonly detections: Detection[];
  readonly detectionLog: Detection[];
  readonly latency: number;
  readonly hasHazard: boolean;
  readonly frameNumber: number;
  readonly error: string | null;
  readonly videoSource: VideoSource;
}

function captureFrame(video: HTMLVideoElement): Promise<Blob | null> {
  return new Promise((resolve) => {
    if (video.readyState < 2 || video.videoWidth === 0) {
      resolve(null);
      return;
    }
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) { resolve(null); return; }
    ctx.drawImage(video, 0, 0);
    canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.85);
  });
}

export function useDigitalTwin(
  videoRef: React.RefObject<HTMLVideoElement | null>,
  intervalMs = 1500,
) {
  const [state, setState] = useState<DigitalTwinState>({
    isRunning: false,
    detections: [],
    detectionLog: [],
    latency: 0,
    hasHazard: false,
    frameNumber: 0,
    error: null,
    videoSource: 'none',
  });

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const webcamStreamRef = useRef<MediaStream | null>(null);
  const runningRef = useRef(false);
  runningRef.current = state.isRunning;

  const performInference = useCallback(async () => {
    if (!runningRef.current) return;

    const video = videoRef.current;
    if (!video || video.readyState < 2 || video.videoWidth === 0) {
      return;
    }

    const t0 = performance.now();
    try {
      const blob = await captureFrame(video);
      if (!blob) return;

      const results = await fetchDetections(blob);
      const latency = Math.round(performance.now() - t0);
      setState((prev) => ({
        ...prev,
        detections: results,
        detectionLog:
          results.length > 0
            ? [...results, ...prev.detectionLog].slice(0, 50)
            : prev.detectionLog,
        latency,
        hasHazard: results.some((d) => d.hazardous),
        frameNumber: prev.frameNumber + 1,
        error: null,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        detections: [],
        error: err instanceof Error ? err.message : 'Inference failed',
      }));
    }
  }, [videoRef]);

  useEffect(() => {
    if (state.isRunning) {
      performInference();
      intervalRef.current = setInterval(performInference, intervalMs);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [state.isRunning, intervalMs, performInference]);

  const startWebcam = useCallback(async () => {
    try {
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' },
          audio: false,
        });
      } catch {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        });
      }
      webcamStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setState((s) => ({ ...s, isRunning: true, videoSource: 'webcam', error: null }));
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setState((s) => ({
        ...s,
        error: msg.includes('NotAllowed') || msg.includes('Permission')
          ? 'Camera permission denied. Please allow camera access in your browser settings.'
          : `Camera error: ${msg}`,
      }));
    }
  }, [videoRef]);

  const loadVideo = useCallback((file: File) => {
    if (!videoRef.current) return;
    const url = URL.createObjectURL(file);
    videoRef.current.srcObject = null;
    videoRef.current.src = url;
    videoRef.current.loop = true;
    videoRef.current.play().catch(() => {});
    setState((s) => ({ ...s, isRunning: true, videoSource: 'upload', error: null }));
  }, [videoRef]);

  const start = useCallback(() => {
    setState((s) => ({ ...s, isRunning: true }));
  }, []);

  const stop = useCallback(() => {
    setState((s) => ({ ...s, isRunning: false, detections: [] }));
  }, []);

  const reset = useCallback(() => {
    if (webcamStreamRef.current) {
      webcamStreamRef.current.getTracks().forEach((t) => t.stop());
      webcamStreamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
      videoRef.current.src = '';
    }
    setState({
      isRunning: false,
      detections: [],
      detectionLog: [],
      latency: 0,
      hasHazard: false,
      frameNumber: 0,
      error: null,
      videoSource: 'none',
    });
  }, [videoRef]);

  return { ...state, start, stop, reset, startWebcam, loadVideo };
}
