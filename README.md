# Nighty Code Generation Server

A local server that uses OpenRouter's API to generate code for Nighty scripts. This server acts as a bridge between Nighty and various AI models available through OpenRouter.

## Features

- Code generation using OpenRouter's API
- Support for multiple AI models
- Automatic code block formatting
- Error handling and logging
- Context-aware generation using project documentation

## Prerequisites

- Node.js 16 or higher
- An OpenRouter API key (get one at https://openrouter.ai/keys)

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Add your OpenRouter API key to the `.env` file
5. Start the server:
   ```bash
   node server.js
   ```

## Usage

The server runs on `http://localhost:3000` by default. It accepts POST requests to `/generate` with the following JSON body:

```json
{
  "prompt": "Your code generation prompt",
  "model": "meta-llama/llama-4-maverick:free",  // Optional
  "language": "python"  // Optional
}
```

## Nighty Integration

To use this with Nighty, place the `generate_code.py` script in your Nighty scripts directory. The script will communicate with this server to generate code.

## Available Models

The server supports all models available through OpenRouter. Some recommended models:
- `meta-llama/llama-4-maverick:free`
- `deepseek/deepseek-chat-v3-0324:free`
- `mistralai/mistral-small-3.1-24b-instruct:free`

## License

MIT License - See LICENSE file for details 