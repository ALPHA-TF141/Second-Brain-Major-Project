import { useEffect, useState } from 'react';

export function useIpcAppInfo() {
  const [appInfo, setAppInfo] = useState({
    name: 'Second Brain',
    phase: 'Phase 1',
    mode: 'browser'
  });

  useEffect(() => {
    if (!window.secondBrain?.getAppInfo) {
      return;
    }

    window.secondBrain.getAppInfo().then(setAppInfo).catch(() => {
      setAppInfo((current) => ({ ...current, mode: 'unknown' }));
    });
  }, []);

  return appInfo;
}
