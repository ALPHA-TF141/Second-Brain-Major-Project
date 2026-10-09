import { apiClient } from './apiClient.js';

export function createChatSocket({ onEvent, onOpen, onClose, onError } = {}) {
  const token = apiClient.getToken();
  if (!token) return null;

  const host = apiClient.baseUrl || (typeof window !== "undefined" ? window.location.origin : "http://127.0.0.1:8000");
  const wsBaseUrl = host.replace(/^http/, "ws");
  const socket = new WebSocket(`${wsBaseUrl}/ws/chat?token=${encodeURIComponent(token)}`);

  socket.onopen = () => onOpen?.(socket);
  socket.onmessage = (event) => {
    try {
      onEvent?.(JSON.parse(event.data));
    } catch {
      onEvent?.({ type: 'raw', content: event.data });
    }
  };
  socket.onclose = onClose;
  socket.onerror = onError;

  return socket;
}
