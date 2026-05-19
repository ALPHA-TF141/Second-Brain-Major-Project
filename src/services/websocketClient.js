import { apiClient } from './apiClient.js';

export function createLiveSocket({ onOpen, onMessage, onClose, onError } = {}) {
  const token = apiClient.getToken();
  if (!token) {
    return null;
  }

  const wsBaseUrl = apiClient.baseUrl.replace(/^http/, 'ws');
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
