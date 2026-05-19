import { createContext, useContext, useMemo, useState } from 'react';

const AssistantContext = createContext(null);

export function AssistantProvider({ children }) {
  const [isAssistantRunning, setIsAssistantRunning] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      title: 'System online',
      message: 'Second Brain shell is ready for Phase 1.'
    }
  ]);

  function toggleAssistant() {
    setIsAssistantRunning((current) => !current);
  }

  function toggleListening() {
    setIsListening((current) => !current);
  }

  function addNotification(title, message) {
    setNotifications((current) => [
      {
        id: Date.now(),
        title,
        message
      },
      ...current.slice(0, 4)
    ]);
  }

  const value = useMemo(
    () => ({
      isAssistantRunning,
      isListening,
      notifications,
      toggleAssistant,
      toggleListening,
      addNotification
    }),
    [isAssistantRunning, isListening, notifications]
  );

  return <AssistantContext.Provider value={value}>{children}</AssistantContext.Provider>;
}

export function useAssistant() {
  const context = useContext(AssistantContext);

  if (!context) {
    throw new Error('useAssistant must be used inside AssistantProvider');
  }

  return context;
}
