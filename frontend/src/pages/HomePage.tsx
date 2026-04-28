import { useRef } from 'react';
import { useDigitalTwin } from '@/hooks/useDigitalTwin';
import { useLogs } from '@/hooks/useLogs';
import { useDispatchQueue } from '@/hooks/useDispatch';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import DetectionScope from '@/components/homepage/DetectionScope';
import ThroughputStats from '@/components/homepage/ThroughputStats';
import ConveyorFeed from '@/components/homepage/ConveyorFeed';
import LiveLogTable from '@/components/homepage/LiveLogTable';
import RecentCaptures from '@/components/homepage/RecentCaptures';
import LiveTerminal from '@/components/homepage/LiveTerminal';
import HazardPosture from '@/components/homepage/HazardPosture';
import DispatchQueue from '@/components/homepage/DispatchQueue';

export default function HomePage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const {
    isRunning,
    detections,
    detectionLog,
    framePreview,
    hasHazard,
    latency,
    frameNumber,
    error,
    videoSource,
    start,
    stop,
    reset,
    startWebcam,
    loadVideo,
  } = useDigitalTwin(videoRef, 700);
  const logs = useLogs(3000);
  const dispatchItems = useDispatchQueue(5000);

  return (
    <div className="flex h-full overflow-hidden">
      {/* LEFT SIDEBAR */}
      <aside className="hidden xl:flex w-72 shrink-0 border-r border-border-dark bg-background-dark flex-col overflow-y-auto">
        <DetectionScope />
        <ThroughputStats />
      </aside>

      {/* CENTER CONTENT */}
      <section className="flex-1 flex flex-col min-w-0 bg-[#06090c]">
        {/* Controls bar */}
        <div className="shrink-0 border-b border-border-dark bg-panel-dark">
          <div className="h-10 flex items-center gap-2 px-4">
          <Sheet>
            <SheetTrigger asChild>
              <button className="xl:hidden text-text-dim hover:text-white mr-2">
                <span className="material-symbols-outlined text-lg">filter_list</span>
              </button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0 pt-10 overflow-y-auto">
              <DetectionScope />
              <ThroughputStats />
            </SheetContent>
          </Sheet>

          {videoSource !== 'none' && (
            <>
              <Button size="sm" onClick={isRunning ? stop : start}>
                <span className="material-symbols-outlined text-sm mr-1">
                  {isRunning ? 'pause' : 'play_arrow'}
                </span>
                {isRunning ? 'Pause' : 'Resume'}
              </Button>
              <Button size="sm" variant="outline" onClick={reset}>
                <span className="material-symbols-outlined text-sm mr-1">refresh</span>
                Reset
              </Button>
            </>
          )}

          {videoSource !== 'none' && (
            <div className="ml-2 flex items-center gap-2 text-[10px] font-mono text-text-dim">
              <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-primary animate-pulse' : 'bg-slate-600'}`} />
              {isRunning ? 'DETECTING' : 'PAUSED'}
              {latency > 0 && <span className="text-primary">({latency}ms)</span>}
            </div>
          )}

          <Sheet>
            <SheetTrigger asChild>
              <button className="lg:hidden ml-auto text-text-dim hover:text-white">
                <span className="material-symbols-outlined text-lg">security</span>
              </button>
            </SheetTrigger>
            <SheetContent side="right" className="w-80 p-0 pt-10 overflow-y-auto">
              <LiveTerminal logs={logs} />
              <HazardPosture hasHazard={hasHazard} />
              <DispatchQueue items={dispatchItems} />
            </SheetContent>
          </Sheet>
          </div>
        </div>

        {/* Video feed */}
        <div className="h-[60%] border-b border-border-dark flex flex-col min-h-0">
          <ConveyorFeed
            detections={detections}
            framePreview={framePreview}
            hasHazard={hasHazard}
            videoRef={videoRef}
            videoSource={videoSource}
            latency={latency}
            frameNumber={frameNumber}
            error={error}
            onStartWebcam={startWebcam}
            onLoadVideo={loadVideo}
          />
        </div>

        {/* Bottom split: log table + captures */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          <div className="w-full md:w-1/2 md:border-r border-border-dark flex flex-col min-h-0">
            <LiveLogTable detections={detectionLog} />
          </div>
          <div className="hidden md:flex w-1/2 flex-col min-h-0">
            <RecentCaptures detections={detectionLog} />
          </div>
        </div>
      </section>

      {/* RIGHT SIDEBAR */}
      <aside className="hidden lg:flex w-80 shrink-0 border-l border-border-dark bg-background-dark flex-col overflow-y-auto">
        <LiveTerminal logs={logs} />
        <HazardPosture hasHazard={hasHazard} />
        <DispatchQueue items={dispatchItems} />
      </aside>
    </div>
  );
}
