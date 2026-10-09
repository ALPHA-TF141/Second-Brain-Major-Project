import { apiClient } from './apiClient.js';

export function createLiveSocket({ onOpen, onMessage, onClose, onError } = {}) {
  const token = apiClient.getToken();
  if (!token) {
    return null;
  }

  const host = apiClient.baseUrl || (typeof window !== "undefined" ? window.location.origin : "http://127.0.0.1:8000");
  const wsBaseUrl = host.replace(/^http/, "ws");
  const socket = new WebSocket(`${wsBaseUrl}/ws/live?token=${encodeURIComponent(token)}`);

  socket.onopen = () => {
    onOpen?.(socket);
    socket.send(JSON.stringify({ message: 'Frontend connected' }));
  };

  socket.onmessage = (event) => {
    try {
      onMessage?.(JSON.parse(event.data));
    } catch {
      onMessage?.({ type: 'raw', message: event.data });
    }
  };

  socket.onclose = onClose;
  socket.onerror = onError;

  return socket;
}
