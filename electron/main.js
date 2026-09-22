const { app, BrowserWindow, ipcMain, session, Tray, Menu, nativeImage, shell, globalShortcut, screen } = require('electron');
const path = require('path');

const isDev = !app.isPackaged;

let mainWindow = null;
let orbWindow = null;
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
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  if (isDev) {
    mainWindow.loadURL('http://127.0.0.1:5173');
    mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
      console.warn(`[Electron] Reconnecting to Vite dev server (${validatedURL})... Retrying in 1.5s`);
      setTimeout(() => {
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.loadURL('http://127.0.0.1:5173');
        }
      }, 1500);
    });
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  // Forward console warnings and errors from React to terminal
  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    if (level >= 2) {
      console.log(`[Renderer Console] ${message} (${sourceId}:${line})`);
    }
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      createTray();
    }
  });

  mainWindow.on('show', () => { if (tray) tray.destroy(); });
}

// ---- Transparent Floating Golden Holographic Orb Window ----
function createOrbWindow() {
  if (orbWindow && !orbWindow.isDestroyed()) return orbWindow;

  const primaryDisplay = screen.getPrimaryDisplay();
  const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;
  const orbW = 380;
  const orbH = 460;
  const orbX = Math.round(screenWidth - orbW - 20);
  const orbY = Math.round(screenHeight - orbH - 20);

  orbWindow = new BrowserWindow({
    width: orbW,
    height: orbH,
    x: orbX,
    y: orbY,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    alwaysOnTop: true,
    skipTaskbar: true,
    hasShadow: false,
    resizable: false,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  const orbUrl = isDev
    ? 'http://127.0.0.1:5173/#/jarvis-orb'
    : `file://${path.join(__dirname, '../dist/index.html')}#/jarvis-orb`;

  orbWindow.loadURL(orbUrl);

  orbWindow.on('closed', () => {
    orbWindow = null;
  });

  return orbWindow;
}

/**
 * Ensure the orb is VISIBLE and awake.
 *
 * Distinct from the Alt+J toggle on purpose: this is called when something
 * wants the user's attention (wake word detected, proactive announcement).
 * Using the toggle here would HIDE the orb whenever it happened to already be
 * on screen - the opposite of the intent.
 */
function revealOrbWindow() {
  if (!orbWindow || orbWindow.isDestroyed()) {
    createOrbWindow();
  }
  if (!orbWindow) return;

  if (!orbWindow.isVisible()) {
    orbWindow.show();
  }
  orbWindow.focus();
  orbWindow.webContents.send('jarvis:wake');
}

function toggleOrbWindow() {
  if (!orbWindow || orbWindow.isDestroyed()) {
    createOrbWindow();
  }
  if (!orbWindow) return;

  if (orbWindow.isVisible()) {
    orbWindow.hide();
  } else {
    revealOrbWindow();
  }
}

// ---- Mic + notifications permission ----
function setupPermissions() {
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    return callback(true);
  });
  session.defaultSession.setPermissionCheckHandler(() => true);
}

function trayIcon() {
  let img = nativeImage.createFromPath(path.join(__dirname, 'icon.png'));
  if (img.isEmpty()) img = nativeImage.createEmpty();
  return img;
}

function createTray() {
  if (tray) return;
  tray = new Tray(trayIcon());
  tray.setToolTip('Second Brain — Jarvis');
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Summon Jarvis Orb', click: () => toggleOrbWindow() },
    { label: 'Open Command Center', click: () => { mainWindow.show(); mainWindow.focus(); } },
    { type: 'separator' },
    { label: 'Pause capture', click: () => mainWindow.webContents.send('jarvis:capture', 'pause') },
    { label: 'Resume capture', click: () => mainWindow.webContents.send('jarvis:capture', 'resume') },
    { type: 'separator' },
    { label: 'Restart', click: () => { mainWindow.reload(); } },
    { label: 'Open DevTools', click: () => mainWindow.webContents.openDevTools({ mode: 'detach' }) },
    { type: 'separator' },
    { label: 'Quit', click: () => { isQuitting = true; app.quit(); } }
  ]);
  tray.setContextMenu(contextMenu);
  tray.on('click', () => { toggleOrbWindow(); });
}

// ---------------------------------------------------------------------------
// Open external URLs in the user's real browser.
// Google refuses OAuth sign-in inside embedded webviews ("This browser or app
// may not be secure"), so the consent screen MUST open in the system browser.
// Only http/https are allowed - never file:// or custom schemes.
// ---------------------------------------------------------------------------
ipcMain.handle('shell:open-external', async (_event, url) => {
  try {
    const parsed = new URL(String(url));
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return { ok: false, error: 'Only http and https URLs can be opened' };
    }
    await shell.openExternal(parsed.toString());
    return { ok: true };
  } catch (err) {
    return { ok: false, error: String(err) };
  }
});

app.whenReady().then(() => {
  setupPermissions();
  createWindow();
  createOrbWindow();

  // Register Global Jarvis Shortcuts: Alt+Space and Alt+J
  try {
    globalShortcut.register('Alt+J', () => {
      toggleOrbWindow();
    });
    globalShortcut.register('Alt+Space', () => {
      toggleOrbWindow();
    });
  } catch (err) {
    console.warn('Could not register global shortcuts:', err);
  }

  // Only auto-start on Windows boot if the app is packaged as an installed production .exe
  if (app.isPackaged) {
    app.setLoginItemSettings({
      openAtLogin: true,
      path: process.execPath,
      args: []
    });
  } else {
    try {
      app.setLoginItemSettings({
        openAtLogin: false
      });
    } catch {
      // Ignore
    }
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    } else {
      mainWindow.show();
    }
  });
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
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

ipcMain.on('orb:hide', () => {
  if (orbWindow && !orbWindow.isDestroyed()) {
    orbWindow.hide();
  }
});

ipcMain.on('orb:show', () => {
  toggleOrbWindow();
});

// Always reveal (never toggle). Used by the wake word and proactive voice.
ipcMain.on('orb:reveal', () => {
  revealOrbWindow();
});

ipcMain.on('orb:show-main', () => {
  if (mainWindow) {
    mainWindow.show();
    mainWindow.focus();
  }
});
