import { apiClient } from './apiClient.js';

export async function createVoiceSocket({ onEvent, onOpen, onClose, onError } = {}) {
  // Always get a fresh token so we never connect with an expired one
  let token = apiClient.getToken();
  if (!token) {
    await apiClient.login('demo', 'secondbrain');
    token = apiClient.getToken();
  }

  if (!token) return null;

  const wsBaseUrl = apiClient.baseUrl.replace(/^http/, 'ws');
  const socket = new WebSocket(`${wsBaseUrl}/ws/voice?token=${encodeURIComponent(token)}`);

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