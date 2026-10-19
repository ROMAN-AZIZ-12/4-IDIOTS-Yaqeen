// Preview bridge only: retain Python/FastAPI and the existing frontend unchanged.
const { spawnSync, spawn } = require('node:child_process');
const { existsSync } = require('node:fs');
const path = require('node:path');
const windows = process.platform === 'win32';
const python = path.join('backend', '.venv', windows ? 'Scripts/python.exe' : 'bin/python');
function run(command, args) {
  const result = spawnSync(command, args, { stdio: 'inherit' });
  if (result.error || result.status !== 0) {
    console.error('Python setup failed. Python 3.11+ and pip/network access are required.');
    process.exit(result.status || 1);
  }
}
if (process.argv[2] === 'install') {
  if (!existsSync(python)) run(windows ? 'python' : 'python3', ['-m', 'venv', 'backend/.venv']);
  run(python, ['-m', 'pip', 'install', '-r', 'backend/requirements.txt']);
} else {
  if (!existsSync(python)) {
    console.error('Backend virtual environment missing; run npm install first.');
    process.exit(1);
  }
  const backend = spawn(path.resolve(python), ['-m', 'uvicorn', 'app.main:app',
    '--host', '0.0.0.0', '--port', process.env.PORT || '8000'],
    { cwd: 'backend', stdio: 'inherit', env: process.env });
  const viteCommand = windows ? 'npx.cmd' : 'npx';
  const frontend = spawn(viteCommand, ['vite', '--host', '0.0.0.0'],
    { stdio: 'inherit', env: process.env });
  const stop = () => { backend.kill('SIGTERM'); frontend.kill('SIGTERM'); };
  for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, stop);
  backend.on('error', () => { console.error('Could not launch Python backend.'); stop(); process.exit(1); });
  frontend.on('error', () => { console.error('Could not launch Vite frontend.'); stop(); process.exit(1); });
  backend.on('exit', code => { if (code && code !== 0) frontend.kill('SIGTERM'); });
  frontend.on('exit', code => { if (code && code !== 0) backend.kill('SIGTERM'); });
}
