import { apiClient } from './apiClient.js';

export function createChatSocket({ onEvent, onOpen, onClose, onError } = {}) {
  const token = apiClient.getToken();
  if (!token) return null;

  const wsBaseUrl = apiClient.baseUrl.replace(/^http/, 'ws');
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
