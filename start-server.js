import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { getScriptsPath } from './utils.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Get the scripts path from Nighty
const scriptsPath = getScriptsPath();

// Start the server with the correct environment variable
const server = spawn('node', ['server.js'], {
  env: {
    ...process.env,
    SCRIPTS_PATH: scriptsPath
  },
  cwd: __dirname
});

// Log server output
server.stdout.on('data', (data) => {
  console.log(`Server: ${data}`);
});

server.stderr.on('data', (data) => {
  console.error(`Server Error: ${data}`);
});

server.on('close', (code) => {
  console.log(`Server process exited with code ${code}`);
}); 