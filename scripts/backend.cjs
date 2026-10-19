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
  const child = spawn(path.resolve(python), ['-m', 'uvicorn', 'app.main:app',
    '--host', '0.0.0.0', '--port', process.env.PORT || '8000'],
    { cwd: 'backend', stdio: 'inherit', env: process.env });
  for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
  child.on('error', () => { console.error('Could not launch Python backend.'); process.exit(1); });
  child.on('exit', code => process.exit(code || 0));
}
