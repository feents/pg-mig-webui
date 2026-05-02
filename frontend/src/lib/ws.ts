export function createMigrationWS(
  jobId: number,
  onMessage: (data: { progress_pct: number; status: string; log: string }) => void,
  onClose?: () => void
): WebSocket {
  const token = localStorage.getItem("access_token") ?? "";
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${protocol}://${window.location.host}/ws/migrations/${jobId}?token=${token}`);

  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data));
    } catch {
      // ignore parse errors
    }
  };

  ws.onclose = () => onClose?.();

  return ws;
}
