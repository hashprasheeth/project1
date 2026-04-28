type DebugPayload = {
  location: string;
  message: string;
  data?: Record<string, unknown>;
};

export function sendDebugLog(payload: DebugPayload) {
  fetch('/api/debug/client-log', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).catch(() => {
    // Ignore debug log delivery failures.
  });
}
