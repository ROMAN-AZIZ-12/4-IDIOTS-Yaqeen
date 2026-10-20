// Preview bridge only: retain Python/FastAPI and the existing frontend unchanged.
const { spawnSync, spawn } = require('node:child_process');
const { existsSync } = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
process.chdir(root);
const windows = process.platform === 'win32';
const python = path.join(root, 'backend', '.venv', windows ? 'Scripts/python.exe' : 'bin/python');
function run(command, args) {
  const result = spawnSync(command, args, { cwd: root, stdio: 'inherit' });
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
  // Use the backend settings loader without exporting dotenv secrets to Vite.
  const configuration = spawnSync(python, ['-m', 'app.config'], {
    cwd: path.join(root, 'backend'), stdio: 'inherit', env: process.env,
  });
  if (configuration.error) {
    console.error('Could not run the backend configuration check.');
    process.exit(1);
  }
  if (configuration.status !== 0) process.exit(configuration.status || 1);
  if (process.argv[2] === 'check') process.exit(0);
  let viteCli;
  try {
    const vitePackage = require.resolve('vite/package.json', {
      paths: [root, path.join(root, 'frontend')],
    });
    viteCli = path.join(path.dirname(vitePackage), 'bin', 'vite.js');
  } catch {
    console.error('Local Vite installation missing; run npm.cmd install in frontend on Windows, or npm install elsewhere.');
    process.exit(1);
  }
  const backend = spawn(python, ['-m', 'uvicorn', 'app.main:app',
    '--host', '0.0.0.0', '--port', process.env.PORT || '8000'],
    { cwd: path.join(root, 'backend'), stdio: 'inherit', env: process.env });
  const frontend = spawn(process.execPath, [viteCli, '--host', '0.0.0.0',
    '--config', path.join(root, 'frontend', 'vite.config.js')],
    { cwd: root, stdio: 'inherit', env: process.env });
  const stop = () => { backend.kill('SIGTERM'); frontend.kill('SIGTERM'); };
  for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, stop);
  backend.on('error', () => { console.error('Could not launch Python backend.'); stop(); process.exit(1); });
  frontend.on('error', () => { console.error('Could not launch Vite frontend.'); stop(); process.exit(1); });
  backend.on('exit', code => { if (code && code !== 0) frontend.kill('SIGTERM'); });
  frontend.on('exit', code => { if (code && code !== 0) backend.kill('SIGTERM'); });
}
