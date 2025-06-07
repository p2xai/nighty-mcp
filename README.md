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
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Install Python packages from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
4. Add your OpenRouter API key to the `.env` file
5. Start the server:
   ```bash
   node server.js
   ```

## Python Dependencies

The helper scripts such as `channel_importer.py` and `product_formatter.py`
require Python 3 with several libraries installed. Install them using:

```bash
pip install -r requirements.txt
```

This file includes `requests`, `discord.py` and `emoji`. If `requests` is not
available, product formatting will fall back to a basic "Unknown" result when
querying the local MCP server.

## Logging Helper

Nighty may patch Python's ``print`` function to accept a ``type_`` keyword
for log levels. The ``logging_helper.log`` utility checks for this support
and falls back to a regular ``print`` call when the keyword is not
available.

Use this helper instead of calling ``print(..., type_=...)`` directly so your
scripts work whether or not Nighty has patched ``print``.

```python
from logging_helper import log

log("Script initialization complete", type_="INFO")
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

## Running Tests

Unit tests are located in the `tests/` directory and can be executed with
[`pytest`](https://docs.pytest.org/en/stable/):

```bash
pytest
```

This will run the suite of Python tests verifying helper functions such as the
product formatter utilities.

## License

MIT License - See LICENSE file for details 
