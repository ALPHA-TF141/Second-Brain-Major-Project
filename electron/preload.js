const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('secondBrain', {
  getAppInfo: () => ipcRenderer.invoke('app:get-info'),
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close')
});
