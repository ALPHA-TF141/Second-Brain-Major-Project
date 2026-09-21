const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('secondBrain', {
  getAppInfo: () => ipcRenderer.invoke('app:get-info'),
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
  hideOrb: () => ipcRenderer.send('orb:hide'),
  showOrb: () => ipcRenderer.send('orb:show'),
  showMain: () => ipcRenderer.send('orb:show-main'),
  onCaptureCommand: (callback) => {
    ipcRenderer.on('jarvis:capture', (_event, command) => callback(command));
  },
  onSpotlightToggle: (callback) => {
    ipcRenderer.on('jarvis:spotlight', () => callback());
  },
  onWakeTrigger: (callback) => {
    ipcRenderer.on('jarvis:wake', () => callback());
  }
});
