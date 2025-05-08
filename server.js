import express from 'express';
import dotenv from 'dotenv';
import cors from 'cors';
import fetch from 'node-fetch';
import fs from 'fs';
import path from 'path';

dotenv.config();
const app = express();
app.use(cors());
app.use(express.json());

const CONTEXT_PATH = './context/prompt v3.md';

// Add error logging middleware
app.use((err, req, res, next) => {
  console.error('Server Error:', err);
  res.status(500).json({ error: err.message });
});

app.post('/generate', async (req, res) => {
  const { prompt, model = "meta-llama/llama-4-maverick:free", language } = req.body;

  if (!prompt) return res.status(400).json({ error: "Missing prompt." });

  // Check if API key exists
  if (!process.env.OPENROUTER_API_KEY) {
    console.error('OpenRouter API key is missing');
    return res.status(500).json({ error: "OpenRouter API key is not configured" });
  }

  let context = '';
  try {
    context = fs.readFileSync(CONTEXT_PATH, 'utf8');
  } catch (err) {
    console.error('Context file error:', err);
    return res.status(500).json({ error: `Failed to read context file: ${err.message}` });
  }

  const fullPrompt = `
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
7. ALWAYS add a unique_script_function() at the end to call the script and not interfere with other scripts

Example:
\`\`\`python
import json
import discord

@nightyScript(
    name="Script Name",
    author="thedorekaczynski",
    description="Description",
    usage="<p>command"
)
def unqiue_script_function():
    """
    SCRIPT NAME
    ----------
    Description
    
    COMMANDS:
    <p>command - Description
    
    EXAMPLES:
    <p>command - Example
    
    NOTES:
    - Important notes
    """
    @bot.command(
        name="command",
        description="Description"
    )
    async def command_handler(ctx, *, args: str):
        try:
            # Command logic
            await ctx.send("Result")
        except Exception as e:
            await ctx.send(f"Error: {e}")

unique_script_function()
\`\`\`

Context:
---
${context}
---

Prompt: ${prompt}

Generate ${language || 'python'} code. Return ONLY the code block.
`.trim();

  try {
    console.log('Sending request to OpenRouter...');
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
        messages: [{ role: 'user', content: fullPrompt }],
        temperature: 0.3,
        max_tokens: 4096  // Increase max tokens for larger responses
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('OpenRouter API error:', errorData);
      throw new Error(`OpenRouter API error: ${errorData.error?.message || response.statusText}`);
    }

    const data = await response.json();
    let output = data.choices?.[0]?.message?.content || "[No output returned]";

    // Log response details for debugging
    console.log('Response details:', {
      finish_reason: data.choices?.[0]?.finish_reason,
      content_length: output.length,
      has_code_block: output.includes("```"),
      model: model
    });

    // Check if response was truncated
    if (data.choices?.[0]?.finish_reason === "length") {
      console.warn('Response was truncated due to length limit');
      output += "\n\n[Note: Response was truncated due to length limit. Consider breaking down the request into smaller parts.]";
    }

    // Validate the response format
    if (!output.includes("```")) {
      console.warn('Response missing code block markers');
      output = "```python\n" + output + "\n```";
    }

    res.json({ output });

  } catch (err) {
    console.error('LLM call error:', err);
    res.status(500).json({ error: `LLM call failed: ${err.message}` });
  }
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
});
