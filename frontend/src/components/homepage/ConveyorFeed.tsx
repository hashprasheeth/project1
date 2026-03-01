import { useRef, useCallback } from 'react';
import type { Detection } from '@/data/types';
import type { VideoSource } from '@/hooks/useDigitalTwin';
import { cn } from '@/lib/utils';

interface ConveyorFeedProps {
  readonly detections: Detection[];
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

export default function ConveyorFeed({
  detections,
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

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onLoadVideo(file);
    },
    [onLoadVideo],
  );

  const hazardCount = detections.filter((d) => d.hazardous).length;

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

      <div className="relative flex-1 bg-black border border-border-dark overflow-hidden min-h-[200px]">
        {/* Video element */}
        <video
          ref={videoRef}
          className={cn(
            'absolute inset-0 w-full h-full object-contain bg-black',
            videoSource === 'none' && 'hidden',
          )}
          muted
          playsInline
        />

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

        {/* Bounding boxes overlay */}
        {detections.map((d) => (
          <div
            key={d.id}
            className={cn('absolute border-2 z-20', getBorderColor(d))}
            style={{
              left: `${d.bbox.x * 100}%`,
              top: `${d.bbox.y * 100}%`,
              width: `${d.bbox.w * 100}%`,
              height: `${d.bbox.h * 100}%`,
            }}
          >
            <div className={cn('absolute -top-5 left-0 text-black text-[10px] font-bold px-1 whitespace-nowrap', getLabelBg(d))}>
              {d.className.replace(/-/g, ' ')} ({Math.round(d.confidence * 100)}%)
            </div>
          </div>
        ))}

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
