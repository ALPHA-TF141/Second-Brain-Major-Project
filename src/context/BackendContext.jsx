import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { apiClient } from '../services/apiClient.js';
import { createLiveSocket } from '../services/websocketClient.js';

const BackendContext = createContext(null);

export function BackendProvider({ children }) {
  const [apiStatus, setApiStatus] = useState('checking');
  const [socketStatus, setSocketStatus] = useState('disconnected');
  const [username, setUsername] = useState('Immanuel');
  const [lastLiveMessage, setLastLiveMessage] = useState(null);
  const [liveEvents, setLiveEvents] = useState([]);
  const socketRef = useRef(null);

  async function checkHealth() {
    setApiStatus('checking');
    try {
      await apiClient.health();
      setApiStatus('online');
    } catch {
      setApiStatus('offline');
    }
  }

  async function loginDemo(user = 'Immanuel') {
    try {
      const data = await apiClient.login(user, 'secondbrain');
      setUsername(data.username || 'Immanuel');
      setApiStatus('authenticated');
      connectSocket();
      return data;
    } catch {
      setUsername('Immanuel');
      return null;
    }
  }

  async function logout() {
    try {
      await apiClient.logout();
    } finally {
      socketRef.current?.close();
      socketRef.current = null;
      setUsername('Immanuel');
      setSocketStatus('disconnected');
      await checkHealth();
    }
  }

  function connectSocket() {
    socketRef.current?.close();
    setSocketStatus('connecting');

    const socket = createLiveSocket({
      onOpen: () => setSocketStatus('connected'),
      onMessage: (message) => {
        setLastLiveMessage(message);
        setLiveEvents((current) => [message, ...current].slice(0, 30));
      },
      onClose: () => setSocketStatus('disconnected'),
      onError: () => setSocketStatus('error')
    });

    if (!socket) {
      setSocketStatus('disconnected');
      return;
    }

    socketRef.current = socket;
  }

  useEffect(() => {
    // 100% Silent Automatic Login on App Boot!
    async function boot() {
      await loginDemo('Immanuel');
      await checkHealth();
    }
    boot();

    // Auto-retry health check every 4 seconds so it turns "online" as soon as backend finishes booting
    const timer = setInterval(() => {
      apiClient.health()
        .then(() => {
          setApiStatus((prev) => (prev === 'offline' || prev === 'checking' ? 'authenticated' : prev));
          if (!apiClient.getToken()) loginDemo('Immanuel');
        })
        .catch(() => setApiStatus('offline'));
    }, 4000);

    return () => {
      clearInterval(timer);
      socketRef.current?.close();
    };
  }, []);

  const value = useMemo(
    () => ({
      apiStatus,
      socketStatus,
      username,
      lastLiveMessage,
      liveEvents,
      checkHealth,
      loginDemo,
      logout,
      connectSocket,
      apiClient
    }),
    [apiStatus, socketStatus, username, lastLiveMessage, liveEvents]
  );

  return <BackendContext.Provider value={value}>{children}</BackendContext.Provider>;
}

export function useBackend() {
  const context = useContext(BackendContext);

  if (!context) {
    throw new Error('useBackend must be used inside BackendProvider');
  }

  return context;
}
