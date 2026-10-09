const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const isWin = process.platform === 'win32';
const venvPython = isWin
  ? path.join(__dirname, 'backend', '.venv', 'Scripts', 'python.exe')
  : path.join(__dirname, 'backend', '.venv', 'bin', 'python');

const pythonCmd = fs.existsSync(venvPython) ? venvPython : (isWin ? 'python' : 'python3');

console.log(`[Jarvis Backend] Launching backend with: ${pythonCmd}`);

const proc = spawn(
  pythonCmd,
  ['-m', 'uvicorn', 'app.main:app', '--reload', '--host', '127.0.0.1', '--port', '8000'],
  {
    cwd: path.join(__dirname, 'backend'),
    stdio: 'inherit',
    shell: false
  }
);

proc.on('error', (err) => {
  console.error('[Jarvis Backend] Failed to start backend process:', err);
});

proc.on('close', (code) => {
  process.exit(code || 0);
});
