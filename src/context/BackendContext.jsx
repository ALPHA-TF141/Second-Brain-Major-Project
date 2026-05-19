import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { apiClient } from '../services/apiClient.js';
import { createLiveSocket } from '../services/websocketClient.js';

const BackendContext = createContext(null);

export function BackendProvider({ children }) {
  const [apiStatus, setApiStatus] = useState('checking');
  const [socketStatus, setSocketStatus] = useState('disconnected');
  const [username, setUsername] = useState('');
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

  async function loginDemo() {
    const data = await apiClient.login();
    setUsername(data.username);
    setApiStatus('authenticated');
    connectSocket();
    return data;
  }

  async function logout() {
    try {
      await apiClient.logout();
    } finally {
      socketRef.current?.close();
      socketRef.current = null;
      setUsername('');
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
    checkHealth();

    return () => {
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
