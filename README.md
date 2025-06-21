# Nighty Code Generation Server
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/p2xai/nighty-mcp)

A local server that uses OpenRouter's API to generate code for Nighty scripts. This server acts as a bridge between Nighty and various AI models available through OpenRouter.

## Features

- **AI-Powered Coding**: Leverage dozens of models via OpenRouter for code generation and fixing.
- **Live Log Viewer**: A web-based UI at `http://localhost:3000/logs` shows all server requests, including pending tasks, AI response times, and generated file paths.
- **Code Versioning**: Automatically saves every generated script to a `versions/` directory, preventing data loss.
- **Context-Aware Prompts**: Uses local documentation files (`context/`) to provide the AI with relevant context for more accurate code generation.
- **Cross-Platform**: Works on Windows, macOS, and Linux.

## Setup

1.  **Prerequisites**: Make sure you have [Node.js](https://nodejs.org/) (v16+) installed.

2.  **Clone the Repository**:
    ```bash
    git clone <your-repo-url>
    cd nighty-mcp
    ```

3.  **Install Dependencies**:
    ```bash
    npm install
    ```

4.  **Configure Environment**:
    -   Create a `.env` file by copying the example: `cp .env.example .env`
    -   Open the `.env` file and add your [OpenRouter API key](https://openrouter.ai/keys).
    -   (Optional) Set the `SCRIPTS_PATH` to your desired output directory for generated scripts.

5.  **Start the Server**:
    ```bash
    node server.js
    ```
    The server will now be running at `http://localhost:3000`.

## Usage

### Live Log Viewer

Navigate to **http://localhost:3000/logs** in your browser to see a live, auto-updating table of all server activity. Requests to `/generate` and `/fixcode` will appear instantly as "pending" and update upon completion.

### API Endpoints

The server exposes the following endpoints for programmatic use:

-   `POST /generate`: Generates a new script.
-   `POST /fixcode`: Fixes an existing piece of code.
-   `GET /api/logs`: Returns the raw log data as JSON.

**Example Request Body**:
```json
{
  "prompt": "Create a python script that prints hello world",
  "model": "meta-llama/llama-3-8b-instruct:free",
  "language": "python",
  "code": "print('hello')" // Only for /fixcode
}
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
