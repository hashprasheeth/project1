import type { Detection } from '@/data/types';

const CAPTURE_IMAGES: Record<string, string> = {
  'battery': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAcLsCVQ39OD-B_WfL_0vqKg7urq5ZunK2vCOiDTwvr5Fv6EWDIHd8RTAbYdJoOO6YoGbYiXsyZhdErKgn0mtI2mL6z6qa0vFITHenn8ztzd88sU5NCNExCifRu9O1nqZvQ-R6pwAv67C_rS0BtAuXEFXJqW5AyMdkcq0oTe9CDO7vrvkIJtfxNkld8qmZ9aNlsdfj8tQlvcMDSs7aCi1HfohUgm2q6lsT3rg5sS3YCE3-PuDFjSiui5x274UvLBHBNGkpiFYRMgP9X',
  'crt': 'https://lh3.googleusercontent.com/aida-public/AB6AXuDw8--ZIpuvkwvnJupSFTVHqYtmWaUGwh1HYTxcYj44ywfn_R9sm2auhx9yb-nO2VK6IIP0YQJK0zrgTyox_PHIq33NSI7XaVrS9WaRFllfOOkzuQ5zOGnJRdZtKgIZnfQYsDZGGcX0HeJF-7P2CinYZ6kk4DY0nDk2EOtTCs06vEumhu5MaqDzhiqoGvXfKkmLyFNAv-A6cFzr_pCM6gMhOB-sxod-CeeFHk9FDL8qRaljQLhpjGbF1MvUDDd94D4FEjRjLRempTmH',
  'calculator': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAgvSz5HgJHHbyfau3jvPF07Xgzl8KEFmHMUS6hoqQ8sAV4vrTc0a5SDgDO33wB9VmkRuDUu7bRanynC882TONPLcoirlOKs0Zi_H2nes3L6zjDhpJTx2iJdJ5xe_F8o4jsCJF6jq5fZeeZhDdGIL-BKZAb6zkH1qz1qN8d64zJI12EIwJ0Zyg7CDWLcax1fHe77645uTgzt2Eje_DSKf6862x2dVWI7z_NgmQqGDQHDZvLmKWuTrbxuQ5-xrbTct1uBK6-euigxnJI',
  'pcb': 'https://lh3.googleusercontent.com/aida-public/AB6AXuBMY7APL9MDFeIZOnYi7ZSSCE_e_62gJwMIxZCLP6UDXRrGUOLYr5EnINyzrWSOURMX9K0qfj0pS_02xbUJsOubt1v4to24aXHcApalAemoNDiub_FYxg9Y9rrdWtm6FOfl53xdKhlV85roNQtJQ6T2hYcUW6Y-B79Uw-94uuf9jVkrAaoatdQuBEW_nPvhHRTMTyjOrd0O0fSYTi0LChEYSkBQdQgq6YERKomeHoO1k_9loRr7494-fWp2UwiZtSp0jYVR7F-W8IL9',
  'plastic': 'https://lh3.googleusercontent.com/aida-public/AB6AXuALwIb5pf710Qwo3hAL1AusadLppKsP1h8c2UFGANZOWYCbiKOy5qZDeTj3hs9_7v3u7urquAYp9ZhXcWHqmxR5bjgUWXdk_qmqcQe9AY_D7RBWvkMoROzTgjY63eAVjlCwxD3HZXyW57Y-KscdeFPUzufzDepUeYjP1GrTyKnmnaDM2ofMWpOx0mDX-tIxKbCk7AHgj8OUd1Pz2AKysVY7zGMdRWKwc-b6KgviKv7nqkCjlNo-vvlEECgBesFqx8Nxsjj_7KXDkeam',
};

interface RecentCapturesProps {
  readonly detections: readonly Detection[];
}

function borderColor(d: Detection): string {
  if (d.hazardous) return 'border-danger';
  if (d.confidence < 0.6) return 'border-warning';
  return 'border-primary';
}

function labelColor(d: Detection): string {
  if (d.hazardous) return 'text-danger';
  if (d.confidence < 0.6) return 'text-warning';
  return 'text-primary';
}

function findImage(className: string): string | undefined {
  const lower = className.toLowerCase();
  for (const [key, url] of Object.entries(CAPTURE_IMAGES)) {
    if (lower.includes(key)) return url;
  }
  return undefined;
}

export default function RecentCaptures({ detections }: RecentCapturesProps) {
  const recent = detections.slice(0, 5);

  return (
    <div className="flex-1 flex flex-col bg-background-dark min-h-0">
      <div className="panel-header">
        <span className="text-[10px] text-text-dim font-bold tracking-widest uppercase">Recent Captures</span>
        <div className="flex gap-2">
          <span className="w-2 h-2 bg-white/20" />
          <span className="w-2 h-2 bg-white/50" />
        </div>
      </div>
      <div className="p-4 grid grid-cols-3 gap-3 overflow-y-auto">
        {recent.map((d) => {
          const imgUrl = findImage(d.className);
          return (
            <div
              key={d.id + d.timestamp}
              className={`aspect-square bg-black border ${borderColor(d)} relative group cursor-pointer hover:border-white transition-colors`}
            >
              {imgUrl ? (
                <img
                  alt={d.className}
                  className="w-full h-full object-cover opacity-80"
                  src={imgUrl}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <span className="material-symbols-outlined text-3xl text-slate-700">image</span>
                </div>
              )}
              {d.hazardous && <div className="absolute inset-0 bg-danger/10" />}
              <div className={`absolute bottom-0 left-0 right-0 bg-black/80 px-2 py-1 text-[9px] font-bold flex justify-between ${labelColor(d)}`}>
                <span>{d.className.replace(/-/g, ' ').slice(0, 8).toUpperCase()}</span>
                <span>{d.timestamp}</span>
              </div>
            </div>
          );
        })}
        {recent.length > 0 && (
          <div className="aspect-square bg-black border border-primary relative cursor-pointer hover:border-white transition-colors flex items-center justify-center">
            <span className="text-text-dim text-[10px]">+ 1,243 MORE</span>
          </div>
        )}
        {recent.length === 0 && (
          <div className="col-span-3 flex items-center justify-center text-text-dim text-xs py-8">
            No captures yet
          </div>
        )}
      </div>
    </div>
  );
}
