const { app, BrowserWindow, ipcMain, session, Tray, Menu, nativeImage, shell } = require('electron');
const path = require('path');
const fs = require('fs');

const isDev = !app.isPackaged;

let mainWindow = null;
let tray = null;
let isQuitting = false;

const APP_ID = 'com.secondbrain.jarvis';

// ---- Windows single instance + auto-start at login ----
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.setAppUserModelId(APP_ID);
  app.on('second-instance', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 640,
    frame: false,
    backgroundColor: '#070A12',
    title: 'Second Brain',
    icon: path.join(__dirname, 'icon.png'), // optional — put an icon.png in electron/
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  if (isDev) {
    mainWindow.loadURL('http://127.0.0.1:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      createTray();
    }
  });

  mainWindow.on('show', () => { if (tray) tray.destroy(); });
}

// ---- Mic + notifications permission ----
function setupPermissions() {
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    return callback(true);
  });
  session.defaultSession.setPermissionCheckHandler(() => true);
}

function trayIcon() {
  // Use a 16x16 empty native image; replace with a real .ico/.png for a visible icon
  let img = nativeImage.createFromPath(path.join(__dirname, 'icon.png'));
  if (img.isEmpty()) img = nativeImage.createEmpty();
  return img;
}

function createTray() {
  if (tray) return;
  tray = new Tray(trayIcon());
  tray.setToolTip('Second Brain — Jarvis');
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Open Second Brain', click: () => { mainWindow.show(); mainWindow.focus(); } },
    { label: 'Pause capture', click: () => mainWindow.webContents.send('jarvis:capture', 'pause') },
    { label: 'Resume capture', click: () => mainWindow.webContents.send('jarvis:capture', 'resume') },
    { type: 'separator' },
    { label: 'Restart', click: () => { mainWindow.reload(); } },
    { label: 'Open DevTools', click: () => mainWindow.webContents.openDevTools({ mode: 'detach' }) },
    { type: 'separator' },
    { label: 'Quit', click: () => { isQuitting = true; app.quit(); } }
  ]);
  tray.setContextMenu(contextMenu);
  tray.on('click', () => { mainWindow.show(); mainWindow.focus(); });
}

app.whenReady().then(() => {
  setupPermissions();
  createWindow();

  // Auto-start with Windows login
  app.setLoginItemSettings({
    openAtLogin: true,
    path: process.execPath,
    args: isDev ? [] : []
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    } else {
      mainWindow.show();
    }
  });
});

app.on('before-quit', () => { isQuitting = true; });
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // keep running in tray
  }
});

// ---- IPC ----
ipcMain.handle('app:get-info', () => ({
  name: 'Second Brain',
  phase: 'Phase 1',
  mode: isDev ? 'development' : 'production'
}));

ipcMain.on('window:minimize', (event) => {
  BrowserWindow.fromWebContents(event.sender)?.minimize();
});

ipcMain.on('window:maximize', (event) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  if (!window) return;
  if (window.isMaximized()) window.unmaximize(); else window.maximize();
});

ipcMain.on('window:close', (event) => {
  BrowserWindow.fromWebContents(event.sender)?.hide();
  createTray();
});