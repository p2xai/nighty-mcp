import express from 'express';
import dotenv from 'dotenv';
import cors from 'cors';
import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import os from 'os';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config();
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

const LOG_LIMIT = 100;
const logs = [];

const CONTEXT_PATH = './context/prompt v3.md';
const UI_DOC_PATH = './context/Nighty UI.md';
const SCRIPTS_PATH = process.env.SCRIPTS_PATH || process.cwd();
const VERSIONS_DIR = path.join(SCRIPTS_PATH, 'versions');
const VERSIONS_JSON = path.join(VERSIONS_DIR, 'versions.json');

// Ensure versions directory exists
if (!fs.existsSync(VERSIONS_DIR)) {
  fs.mkdirSync(VERSIONS_DIR, { recursive: true });
}

// Initialize versions.json if it doesn't exist
if (!fs.existsSync(VERSIONS_JSON)) {
  fs.writeFileSync(VERSIONS_JSON, JSON.stringify({}, null, 2));
}

// Helper to update a log entry when a request completes
function updateLog(id, finalData) {
    const logIndex = logs.findIndex(log => log.id === id);
    if (logIndex === -1) return;

    const updatedLog = { ...logs[logIndex], ...finalData };
    logs[logIndex] = updatedLog;

    console.log(`[${new Date().toISOString()}] <== ${updatedLog.method} ${updatedLog.url} ${updatedLog.status}`);
    if (updatedLog.status !== 'pending' && updatedLog.prompt) {
        console.log(`  > ai response time: ${updatedLog.aiTime}`);
        console.log(`  > generated script: ${updatedLog.file} (${updatedLog.size})`);
    }
}

// Add error logging middleware
app.use((err, req, res, next) => {
  console.error('Server Error:', err);
  res.status(500).json({ error: err.message });
});

// Helper function to extract script name from code
function extractScriptName(code) {
  const scriptNameMatch = code.match(/@nightyScript\s*\(\s*name\s*=\s*["']([^"]+)["']/);
  return scriptNameMatch ? scriptNameMatch[1].trim().replace(/\s+/g, '_').toLowerCase() : `unnamed_script_${Date.now()}`;
}

function formatDuration(ms) {
  const seconds = Math.floor(ms / 1000);
  const milliseconds = ms % 1000;
  return `${seconds}s ${milliseconds}ms`;
}

function shortenPath(fullPath) {
  const homeDir = os.homedir();
  // Use APPDATA on Windows, otherwise fall back to the user's home directory for cleaner paths.
  const rootDir = process.env.APPDATA || homeDir;
  if (fullPath.startsWith(rootDir)) {
    return path.relative(rootDir, fullPath);
  }
  return fullPath;
}

// Helper function to save version
function saveVersion(code, version, scriptName) {
  const versionPath = path.join(VERSIONS_DIR, `${scriptName}_v${version}.py`);
  
  try {
    fs.writeFileSync(versionPath, code);
    
    let versions = {};
    if (fs.existsSync(VERSIONS_JSON)) {
      versions = JSON.parse(fs.readFileSync(VERSIONS_JSON, 'utf8'));
    }
    
    if (!versions[scriptName]) {
      versions[scriptName] = {};
    }
    
    versions[scriptName][version] = {
      timestamp: new Date().toISOString(),
      path: versionPath
    };
    
    fs.writeFileSync(VERSIONS_JSON, JSON.stringify(versions, null, 2));
    return versionPath;
  } catch (error) {
    console.error('Error saving version:', error);
    throw error;
  }
}

// Helper function to get most recent script
function getMostRecentScript() {
  try {
    if (!fs.existsSync(VERSIONS_JSON)) {
      return null;
    }

    const versions = JSON.parse(fs.readFileSync(VERSIONS_JSON, 'utf8'));
    if (Object.keys(versions).length === 0) {
      return null;
    }

    let mostRecentScript = null;
    let mostRecentTime = 0;

    for (const [scriptName, scriptVersions] of Object.entries(versions)) {
      const latestVersion = Math.max(...Object.keys(scriptVersions).map(Number));
      const timestamp = new Date(scriptVersions[latestVersion].timestamp).getTime();
      
      if (timestamp > mostRecentTime) {
        mostRecentTime = timestamp;
        mostRecentScript = {
          name: scriptName,
          version: latestVersion,
          timestamp: scriptVersions[latestVersion].timestamp
        };
      }
    }

    return mostRecentScript;
  } catch (error) {
    console.error('Error getting most recent script:', error);
    return null;
  }
}

// Helper function to determine if prompt is significantly different
function isSignificantlyDifferent(prompt, scriptName) {
  try {
    if (!fs.existsSync(VERSIONS_JSON)) {
      return true;
    }

    const versions = JSON.parse(fs.readFileSync(VERSIONS_JSON, 'utf8'));
    if (!versions[scriptName]) {
      return true;
    }

    // Get the latest version's prompt
    const latestVersion = Math.max(...Object.keys(versions[scriptName]).map(Number));
    const latestPrompt = versions[scriptName][latestVersion].prompt;

    // Simple similarity check - if prompts are very different in length or content
    const lengthDiff = Math.abs(prompt.length - latestPrompt.length) / Math.max(prompt.length, latestPrompt.length);
    if (lengthDiff > 0.5) { // More than 50% difference in length
      return true;
    }

    // Check for significant content differences
    const promptWords = new Set(prompt.toLowerCase().split(/\s+/));
    const latestWords = new Set(latestPrompt.toLowerCase().split(/\s+/));
    const intersection = new Set([...promptWords].filter(x => latestWords.has(x)));
    const similarity = intersection.size / Math.max(promptWords.size, latestWords.size);
    
    return similarity < 0.3; // Less than 30% similar
  } catch (error) {
    console.error('Error checking prompt similarity:', error);
    return true; // If there's an error, treat as different
  }
}

app.post('/generate', async (req, res) => {
  const { prompt, model = "meta-llama/llama-4-maverick:free", language, include_ui = false } = req.body;
  const requestId = Date.now() + Math.random();

  const initialLog = {
    id: requestId,
    timestamp: new Date(),
    method: req.method,
    url: req.url,
    status: 'pending',
    model: model,
    aiTime: '...',
    file: '...',
    size: '...',
    prompt: prompt
  };
  logs.unshift(initialLog);
  console.log(`[${initialLog.timestamp.toISOString()}] ==> ${initialLog.method} ${initialLog.url}`);
  console.log(`  > prompt: "${prompt}"`);

  if (!prompt) return res.status(400).json({ error: "Missing prompt." });
  if (!process.env.OPENROUTER_API_KEY) {
    return res.status(500).json({ error: "OpenRouter API key is not configured" });
  }

  let context = '';
  try {
    context = fs.readFileSync(CONTEXT_PATH, 'utf8');
    if (include_ui) {
      try {
        const uiDoc = fs.readFileSync(UI_DOC_PATH, 'utf8');
        context += "\n\n[UI DOCUMENTATION]\n" + uiDoc;
      } catch (err) {
        console.warn('UI documentation not found:', err.message);
      }
    }
  } catch (err) {
    return res.status(500).json({ error: `Failed to read context file: ${err.message}` });
  }

  const systemPrompt = `
You are an expert developer. Generate code following these rules:
1. Return ONLY the code block, no text before/after
2. Use a single code block with the specified language
3. No nested blocks or extra language tags
4. No explanatory text or comments
5. Follow language conventions
6. For NightyScripts:
   - Include @nightyScript decorator with metadata
   - Add proper docstring with COMMANDS/EXAMPLES/NOTES
   - Add command descriptions
   - Include error handling
   - Add required imports
7. ALWAYS add a unique function to call the script:
   - Function name should be based on the script name (e.g. if script is "file_sender" use "file_sender_script")
   - Convert spaces to underscores and make it lowercase
   - Add "_script" suffix to avoid conflicts
   - Call this function at the end of the file
${include_ui ? `
8. CRITICAL - UI-ONLY SCRIPT REQUIREMENTS:
   - This MUST be a UI-only script - NO text commands or Discord interactions
   - DO NOT use @bot.command or any Discord command decorators
   - DO NOT implement any text-based command handlers
   - DO NOT use ctx.send or any Discord message sending
   - ALL interaction MUST happen through the UI elements
   - The script should ONLY create and manage UI components
   - Use toast notifications instead of text messages for feedback
   - Use status text elements for displaying information
   - Use UI buttons instead of text commands for actions
   - Use UI inputs instead of text arguments for user input
   - Use UI selects instead of text options for choices
   - Use UI groups for organizing related elements
   - Use UI cards for grouping related functionality
   - Use UI containers for layout management
   - ALL user interaction must be through UI elements
   - NO Discord message handling or command processing
   - NO text-based command parsing or argument handling
   - NO text-based response generation
   - NO text-based status updates
   - NO text-based error messages
   - NO text-based success messages
   - NO text-based help or documentation
   - NO text-based configuration
   - NO text-based settings
   - NO text-based options
   - NO text-based parameters
   - NO text-based flags
   - NO text-based arguments
   - NO text-based input
   - NO text-based output
   - NO text-based interaction of any kind` : ''}

Context:
---
${context}
---

Prompt: ${prompt}

Generate ${language || 'python'} code. Return ONLY the code block.
`.trim();

  try {
    const aiRequestStart = Date.now();
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://yourdomain.com',
        'X-Title': 'Nighty MCP'
      },
      body: JSON.stringify({
        model: model,
        messages: [{ role: 'user', content: systemPrompt }],
        temperature: 0.3,
        max_tokens: 4096
      })
    });
    const aiRequestDuration = Date.now() - aiRequestStart;

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`OpenRouter API error: ${errorData.error?.message || response.statusText}`);
    }

    const data = await response.json();
    let output = data.choices?.[0]?.message?.content || "[No output returned]";

    const codeBlockMatch = output.match(/```(?:[a-zA-Z]+)?\n([\s\S]*?)```/s);
    if (codeBlockMatch && codeBlockMatch[1]) {
      output = codeBlockMatch[1].trim();
    } else {
      output = output.trim();
    }

    const scriptName = extractScriptName(output);
    
    let versions = {};
    if (fs.existsSync(VERSIONS_JSON)) {
      versions = JSON.parse(fs.readFileSync(VERSIONS_JSON, 'utf8'));
    }
    const version = versions[scriptName] ? Object.keys(versions[scriptName]).length + 1 : 1;
    const versionPath = saveVersion(output, version, scriptName);

    const stats = fs.statSync(versionPath);
    const fileSizeInKB = stats.size / 1024;

    updateLog(requestId, {
        status: res.statusCode,
        aiTime: formatDuration(aiRequestDuration),
        file: shortenPath(versionPath),
        size: `${fileSizeInKB.toFixed(2)} kb`
    });

    res.json({ 
      output,
      version,
      versionPath,
      scriptName
    });
  } catch (err) {
    console.error('LLM call error:', err);
    updateLog(requestId, {
        status: 500,
        aiTime: 'Error',
        file: err.message,
        size: ''
    });
    res.status(500).json({ error: `LLM call failed: ${err.message}` });
  }
});

app.post('/fixcode', async (req, res) => {
  const { prompt, code, model = "meta-llama/llama-4-maverick:free", language, include_ui = false } = req.body;
  const requestId = Date.now() + Math.random();

  const initialLog = {
    id: requestId,
    timestamp: new Date(),
    method: req.method,
    url: req.url,
    status: 'pending',
    model: model,
    aiTime: '...',
    file: '...',
    size: '...',
    prompt: prompt
  };
  logs.unshift(initialLog);
  console.log(`[${initialLog.timestamp.toISOString()}] ==> ${initialLog.method} ${initialLog.url}`);
  console.log(`  > prompt: "${prompt}"`);

  if (!prompt) return res.status(400).json({ error: "Missing prompt." });
  if (!code) return res.status(400).json({ error: "Missing code to fix." });
  if (!process.env.OPENROUTER_API_KEY) {
    return res.status(500).json({ error: "OpenRouter API key is not configured" });
  }

  let context = '';
  try {
    context = fs.readFileSync(CONTEXT_PATH, 'utf8');
    if (include_ui) {
      try {
        const uiDoc = fs.readFileSync(UI_DOC_PATH, 'utf8');
        context += "\n\n[UI DOCUMENTATION]\n" + uiDoc;
      } catch (err) {
        console.warn('UI documentation not found:', err.message);
      }
    }
  } catch (err) {
    return res.status(500).json({ error: `Failed to read context file: ${err.message}` });
  }

  const fixPrompt = `
You are an expert developer. Fix and improve the following code based on the prompt.
Rules:
1. Return ONLY the code block, no text before/after
2. Use a single code block with the specified language
3. No nested blocks or extra language tags
4. No explanatory text or comments
5. Follow language conventions
6. For NightyScripts:
   - Include @nightyScript decorator with metadata
   - Add proper docstring with COMMANDS/EXAMPLES/NOTES
   - Add command descriptions
   - Include error handling
   - Add required imports
7. ALWAYS add a unique function at the end to call the script:
   - Function name should be based on the script name (e.g. if script is "file_sender" use "file_sender_script")
   - Convert spaces to underscores and make it lowercase
   - Add "_script" suffix to avoid conflicts
   - Call this function at the end of the file
${include_ui ? `
8. CRITICAL - UI-ONLY SCRIPT REQUIREMENTS:
   - This MUST be a UI-only script - NO text commands or Discord interactions
   - DO NOT use @bot.command or any Discord command decorators
   - DO NOT implement any text-based command handlers
   - DO NOT use ctx.send or any Discord message sending
   - ALL interaction MUST happen through the UI elements
   - The script should ONLY create and manage UI components
   - Use toast notifications instead of text messages for feedback
   - Use status text elements for displaying information
   - Use UI buttons instead of text commands for actions
   - Use UI inputs instead of text arguments for user input
   - Use UI selects instead of text options for choices
   - Use UI groups for organizing related elements
   - Use UI cards for grouping related functionality
   - Use UI containers for layout management
   - ALL user interaction must be through UI elements
   - NO Discord message handling or command processing
   - NO text-based command parsing or argument handling
   - NO text-based response generation
   - NO text-based status updates
   - NO text-based error messages
   - NO text-based success messages
   - NO text-based help or documentation
   - NO text-based configuration
   - NO text-based settings
   - NO text-based options
   - NO text-based parameters
   - NO text-based flags
   - NO text-based arguments
   - NO text-based input
   - NO text-based output
   - NO text-based interaction of any kind` : ''}

Context:
---
${context}
---

Original Code:
\`\`\`${language}
${code}
\`\`\`

Prompt for fixes: ${prompt}

Generate fixed ${language} code. Return ONLY the code block.
`.trim();

  try {
    const aiRequestStart = Date.now();
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://yourdomain.com',
        'X-Title': 'Nighty MCP'
      },
      body: JSON.stringify({
        model: model,
        messages: [{ role: 'user', content: fixPrompt }],
        temperature: 0.3,
        max_tokens: 4096
      })
    });
    const aiRequestDuration = Date.now() - aiRequestStart;

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`OpenRouter API error: ${errorData.error?.message || response.statusText}`);
    }

    const data = await response.json();
    let output = data.choices?.[0]?.message?.content || "[No output returned]";

    const codeBlockMatch = output.match(/```(?:[a-zA-Z]+)?\n([\s\S]*?)```/s);
    if (codeBlockMatch && codeBlockMatch[1]) {
      output = codeBlockMatch[1].trim();
    } else {
      output = output.trim();
    }
    
    const originalScriptName = extractScriptName(code);
    const scriptName = extractScriptName(output) || originalScriptName;

    let versions = {};
    if (fs.existsSync(VERSIONS_JSON)) {
      versions = JSON.parse(fs.readFileSync(VERSIONS_JSON, 'utf8'));
    }
    
    const version = versions[scriptName] ? Object.keys(versions[scriptName]).length + 1 : 1;
    const versionPath = saveVersion(output, version, scriptName);

    const stats = fs.statSync(versionPath);
    const fileSizeInKB = stats.size / 1024;
    
    updateLog(requestId, {
        status: res.statusCode,
        aiTime: formatDuration(aiRequestDuration),
        file: shortenPath(versionPath),
        size: `${fileSizeInKB.toFixed(2)} kb`
    });

    res.json({ 
      output,
      version,
      versionPath,
      scriptName,
      fixedFrom: {
        script: originalScriptName
      }
    });
  } catch (err) {
    console.error('LLM call error:', err);
    updateLog(requestId, {
        status: 500,
        aiTime: 'Error',
        file: err.message,
        size: ''
    });
    res.status(500).json({ error: `LLM call failed: ${err.message}` });
  }
});

app.get('/api/logs', (req, res) => {
  res.json(logs);
});

app.get('/logs', (req, res) => {
  fs.readFile(path.join(__dirname, 'public', 'logs.html'), 'utf8', (err, html) => {
    if (err) {
      return res.status(500).send('could not read log file.');
    }

    const logRows = logs.map(log => `
      <tr>
        <td>${log.timestamp.toLocaleString()}</td>
        <td class="status-${log.status}">${log.status || ''}</td>
        <td>${log.method || ''}</td>
        <td>${log.url || ''}</td>
        <td>${log.duration ? log.duration + 'ms' : ''}</td>
        <td>${log.model || ''}</td>
        <td>${log.aiTime || ''}</td>
        <td>${log.file || ''}</td>
        <td>${log.size || ''}</td>
        <td>${log.prompt || ''}</td>
      </tr>
    `).join('');

    const finalHtml = html.replace('<!-- LOG_ROWS -->', logRows);
    res.send(finalHtml);
  });
});

app.listen(3000, () => {
  console.log('✅ MCP server running at http://localhost:3000');
  console.log('Checking environment...');
  if (!process.env.OPENROUTER_API_KEY) {
    console.error('⚠️ Warning: OPENROUTER_API_KEY is not set in .env file');
  } else {
    console.log('✅ OPENROUTER_API_KEY is configured');
  }
  if (!fs.existsSync(CONTEXT_PATH)) {
    console.error(`⚠️ Warning: Context file not found at ${CONTEXT_PATH}`);
  } else {
    console.log('✅ Context file found');
  }
  if (!fs.existsSync(UI_DOC_PATH)) {
    console.error(`⚠️ Warning: UI documentation file not found at ${UI_DOC_PATH}`);
  } else {
    console.log('✅ UI documentation file found');
  }
});
