import { useRef, useCallback, useEffect, useMemo, useState } from 'react';
import type { CapturedFramePreview, Detection } from '@/data/types';
import type { VideoSource } from '@/hooks/useDigitalTwin';
import { cn } from '@/lib/utils';

interface ConveyorFeedProps {
  readonly detections: Detection[];
  readonly framePreview: CapturedFramePreview | null;
  readonly hasHazard: boolean;
  readonly videoRef: React.RefObject<HTMLVideoElement | null>;
  readonly videoSource: VideoSource;
  readonly latency: number;
  readonly frameNumber: number;
  readonly error: string | null;
  readonly onStartWebcam: () => void;
  readonly onLoadVideo: (file: File) => void;
}

function getBorderColor(d: Detection): string {
  if (d.hazardous) return 'border-danger';
  if (d.confidence < 0.6) return 'border-warning border-dotted';
  return 'border-primary border-dashed';
}

function getLabelBg(d: Detection): string {
  if (d.hazardous) return 'bg-danger';
  if (d.confidence < 0.6) return 'bg-warning';
  return 'bg-primary';
}

type VideoViewport = {
  left: number;
  top: number;
  width: number;
  height: number;
};

export default function ConveyorFeed({
  detections,
  framePreview,
  hasHazard,
  videoRef,
  videoSource,
  latency,
  frameNumber,
  error,
  onStartWebcam,
  onLoadVideo,
}: ConveyorFeedProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const [viewport, setViewport] = useState<VideoViewport>({
    left: 0,
    top: 0,
    width: 0,
    height: 0,
  });

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onLoadVideo(file);
    },
    [onLoadVideo],
  );

  const hazardCount = detections.filter((d) => d.hazardous).length;
  const hasVideo = videoSource !== 'none';
  const hasPreview = Boolean(framePreview?.imageUrl);

  useEffect(() => {
    const updateViewport = () => {
      const stage = stageRef.current;
      const video = videoRef.current;
      if (!stage || !video) {
        return;
      }

      const stageWidth = stage.clientWidth;
      const stageHeight = stage.clientHeight;
      const videoWidth = video.videoWidth;
      const videoHeight = video.videoHeight;

      if (!stageWidth || !stageHeight || !videoWidth || !videoHeight) {
        setViewport({ left: 0, top: 0, width: stageWidth, height: stageHeight });
        return;
      }

      const stageAspect = stageWidth / stageHeight;
      const videoAspect = videoWidth / videoHeight;

      let width = stageWidth;
      let height = stageHeight;
      let left = 0;
      let top = 0;

      if (videoAspect > stageAspect) {
        height = stageWidth / videoAspect;
        top = (stageHeight - height) / 2;
      } else {
        width = stageHeight * videoAspect;
        left = (stageWidth - width) / 2;
      }

      setViewport({ left, top, width, height });
    };

    updateViewport();
    const video = videoRef.current;
    const stage = stageRef.current;

    if (!stage) {
      return;
    }

    const resizeObserver = new ResizeObserver(() => updateViewport());
    resizeObserver.observe(stage);
    video?.addEventListener('loadedmetadata', updateViewport);
    window.addEventListener('resize', updateViewport);

    return () => {
      resizeObserver.disconnect();
      video?.removeEventListener('loadedmetadata', updateViewport);
      window.removeEventListener('resize', updateViewport);
    };
  }, [videoRef, videoSource, frameNumber]);

  const overlayStyle = useMemo(
    () => ({
      left: `${viewport.left}px`,
      top: `${viewport.top}px`,
      width: `${viewport.width}px`,
      height: `${viewport.height}px`,
    }),
    [viewport],
  );

  return (
    <div className="flex-1 flex flex-col p-4 min-h-0">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-primary text-sm font-bold tracking-widest flex items-center gap-2">
          <span className="material-symbols-outlined text-[16px] animate-pulse">videocam</span>
          {videoSource === 'webcam'
            ? 'LIVE CAMERA FEED'
            : videoSource === 'upload'
            ? 'UPLOADED VIDEO FEED'
            : 'CONVEYOR FEED 01 - RAW'}
        </h3>
        <div className="hidden sm:flex gap-2">
          {videoSource !== 'none' && (
            <>
              <span className="text-[10px] bg-black/50 px-2 py-0.5 text-primary border border-primary/30">
                {latency}ms
              </span>
              <span className="text-[10px] bg-black/50 px-2 py-0.5 text-text-dim border border-border-dark">
                F#{frameNumber}
              </span>
            </>
          )}
          <span className="text-[10px] bg-black/50 px-2 py-0.5 text-text-dim border border-border-dark">
            {videoSource === 'webcam' ? 'LIVE' : videoSource === 'upload' ? 'FILE' : 'IDLE'}
          </span>
        </div>
      </div>

      <div ref={stageRef} className="relative flex-1 bg-black border border-border-dark overflow-hidden min-h-[200px]">
        {/* Video element */}
        <video
          ref={videoRef}
          className={cn(
            'absolute inset-0 w-full h-full object-contain bg-black',
            hasPreview && 'opacity-0',
            videoSource === 'none' && 'hidden',
          )}
          muted
          playsInline
        />

        {hasPreview && (
          <img
            alt="Latest detected frame"
            className="absolute inset-0 w-full h-full object-contain bg-black"
            src={framePreview?.imageUrl}
          />
        )}

        {/* Placeholder when no video source */}
        {videoSource === 'none' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-6 z-10">
            <img
              alt="Conveyor belt placeholder"
              className="absolute inset-0 w-full h-full object-cover opacity-20"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuBU68a7_aiPb5ZwH0TirKuOtq79oD6LNFCljp0m2NOeI7M50QJ865xJwxtcEeWTytnMPY28CRyUyU_cVUl2JCTu5NzwdF7n8T7TqxjF-PkRHdGbHaL6L2KQfj4tdGEWSGLgqKwGhxMW3vqQmFeT8DF2Uzn_jkj1bMSbt7CNS5nixY2S5-uB_YkWtNWgUwSFd20S3-EZ2HBl3xlSQ716YQbhdokUH6WuJpEfxoD5z6DkN1VAxbRPsoRHI8R3YV9ALz59uj6zuKW8miD2"
            />
            <div className="relative z-20 flex flex-col items-center gap-4">
              <p className="text-text-dim text-sm font-mono uppercase tracking-widest">
                Select Input Source
              </p>
              <div className="flex gap-3">
                <button
                  onClick={onStartWebcam}
                  className="flex items-center gap-2 px-6 py-3 bg-primary/10 border border-primary/40 text-primary text-xs font-bold uppercase tracking-wider hover:bg-primary hover:text-black transition-all"
                >
                  <span className="material-symbols-outlined text-[18px]">videocam</span>
                  Live Camera
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-2 px-6 py-3 bg-panel-dark border border-border-dark text-text-dim text-xs font-bold uppercase tracking-wider hover:border-primary/50 hover:text-white transition-all"
                >
                  <span className="material-symbols-outlined text-[18px]">upload_file</span>
                  Upload Video
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Scanline overlay */}
        <div className="absolute inset-0 scanlines opacity-30 z-10 pointer-events-none" />

        {/* Coordinate readout */}
        <div className="absolute top-4 left-4 z-20 font-mono text-[10px] text-primary/80">
          {videoSource !== 'none' ? (
            <>
              <p>FRAME: {frameNumber}</p>
              <p>LATENCY: {latency}ms</p>
              <p>OBJECTS: {detections.length}</p>
            </>
          ) : (
            <>
              <p>X: 124.45 Y: 89.22</p>
              <p>ZOOM: 1.2x</p>
              <p>ISO: 800</p>
            </>
          )}
        </div>

        {/* Bounding boxes overlay aligned to the rendered video viewport */}
        {hasVideo && viewport.width > 0 && viewport.height > 0 && (
          <div className="absolute z-20 pointer-events-none" style={overlayStyle}>
            {detections.map((d) => {
              const label = d.className.replace(/-/g, ' ');
              const confidence = `${Math.round(d.confidence * 100)}%`;
              return (
                <div
                  key={d.id}
                  className={cn('absolute border-2 shadow-[0_0_0_1px_rgba(0,0,0,0.45)]', getBorderColor(d))}
                  style={{
                    left: `${d.bbox.x * 100}%`,
                    top: `${d.bbox.y * 100}%`,
                    width: `${d.bbox.w * 100}%`,
                    height: `${d.bbox.h * 100}%`,
                  }}
                >
                  <div
                    className={cn(
                      'absolute left-0 top-0 -translate-y-full max-w-[260px] rounded-sm px-1.5 py-1 text-[10px] font-bold uppercase tracking-wide text-black shadow-md',
                      getLabelBg(d),
                    )}
                  >
                    <div className="truncate">{label}</div>
                    <div className="text-[9px] opacity-90">CONF {confidence}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Error display */}
        {error && (
          <div className="absolute bottom-4 left-4 right-4 z-30 bg-danger/20 border border-danger/50 px-3 py-2 text-danger text-xs font-mono">
            {error}
          </div>
        )}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="video/*"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Hazard alert banner */}
      {hasHazard && (
        <div className="mt-2 h-10 bg-danger/10 border border-danger/40 flex items-center justify-center gap-3 animate-pulse">
          <span className="material-symbols-outlined text-danger">gpp_maybe</span>
          <span className="text-danger font-bold tracking-[0.2em] text-xs sm:text-sm">
            SAFETY INTERLOCK — {hazardCount} HAZARDOUS ITEM{hazardCount !== 1 ? 'S' : ''} DETECTED
          </span>
          <span className="material-symbols-outlined text-danger">gpp_maybe</span>
        </div>
      )}
    </div>
  );
}
