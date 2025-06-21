import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export function getScriptsPath() {
  try {
    // Try to get the scripts path from Nighty's environment
    const scriptsPath = execSync('echo %APPDATA%\\Nighty Selfbot\\data\\scripts', { shell: true }).toString().trim();
    return scriptsPath;
  } catch (error) {
    console.error('Error getting scripts path:', error);
    // Fallback to the current directory
    return __dirname;
  }
} 