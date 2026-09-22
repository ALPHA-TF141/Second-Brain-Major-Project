const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('secondBrain', {
  getAppInfo: () => ipcRenderer.invoke('app:get-info'),
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
  hideOrb: () => ipcRenderer.send('orb:hide'),
  showOrb: () => ipcRenderer.send('orb:show'),
  // Always bring the orb up (never toggles it away) - used by wake-word and
  // proactive announcements.
  revealOrb: () => ipcRenderer.send('orb:reveal'),
  showMain: () => ipcRenderer.send('orb:show-main'),
  onCaptureCommand: (callback) => {
    ipcRenderer.on('jarvis:capture', (_event, command) => callback(command));
  },
  onSpotlightToggle: (callback) => {
    ipcRenderer.on('jarvis:spotlight', () => callback());
  },
  onWakeTrigger: (callback) => {
    // Returns an unsubscribe function so re-mounts (HMR, reloads) do not stack
    // duplicate listeners on the same IPC channel.
    const handler = () => callback();
    ipcRenderer.on('jarvis:wake', handler);
    return () => ipcRenderer.removeListener('jarvis:wake', handler);
  },
  // Opens a URL in the user's REAL default browser. Used for the Google OAuth
  // consent screen - Google blocks sign-in inside embedded webviews, so this
  // must hand off to the actual browser.
  openExternal: (url) => ipcRenderer.invoke('shell:open-external', url)
});
