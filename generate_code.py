from pathlib import Path
import requests               # synchronous HTTP client
import asyncio
import discord
import re
import json
import os
from datetime import datetime


@nightyScript(
    name="Generate Code",
    author="thedorekaczynski", 
    description="Generate source‑code by sending a prompt and project docs to a local MCP server (OpenRouter backend).",
    usage="<p>gencode --model <model> --lang <language> <prompt> OR <p>fixcode --model <model> --lang <language> <prompt>"
)
def generate_code_script():
    """
    GENERATE CODE
    -------------
    Sends a user prompt plus bundled project documentation (prompt‑v3.md) to the MCP server
    at http://localhost:3000/generate and returns the generated code.

    COMMANDS:
        <p>gencode --model <model> --lang <language> <prompt>
            --model <model>   Optional. Example: gpt-4, claude-3-opus, mistralai/mistral-7b-instruct:free
            --lang  <lang>    Optional. Language hint for formatting the fenced code block. Default: python.
            <prompt>          Required. Natural‑language request for the code you want.

        <p>fixcode --model <model> --lang <language> <prompt>
            --model <model>   Optional. Example: gpt-4, claude-3-opus, mistralai/mistral-7b-instruct:free
            --lang  <lang>    Optional. Language hint for formatting the fenced code block. Default: python.
            <prompt>          Required. Natural‑language request for code fixes.

    EXAMPLES:
        <p>gencode build a simple flask api
        <p>gencode --model gpt-4 --lang js build a websocket server
        <p>fixcode add error handling to the api endpoints
        <p>fixcode --model gpt-4 optimize the database queries

    NOTES:
    - Uses *requests* wrapped with run_in_thread to avoid blocking Nighty's event loop.
    - Reads context from scripts/project-context/prompt-v3.md each time.
    - Output <1 900 chars returned as fenced block; else attached as file.
    - Versions are automatically saved and incremented.
    """

    # ---------- Helper: run blocking IO in a thread ---------- #
    async def run_in_thread(func, *args, **kwargs):
        """Run sync function in a thread to keep the loop free."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    # ---------- Helper: clean up response ---------- #
    def clean_response(text: str) -> str:
<<<<<<< HEAD
        """Clean up the response by removing explanatory text and fixing code blocks."""
        # If the response contains code blocks, extract the code from the last one
        if "```" in text:
            # Find the last code block - support any language tag, not just python
            code_blocks = re.findall(r"```(?:[a-zA-Z]+)?\n(.*?)```", text, re.DOTALL)
=======
        """Extract the final code block from the response if present.

        If the detected code block is empty, fall back to returning the raw
        response so that potential error messages aren't lost.
        """
        if "```" in text:
            code_blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
>>>>>>> 8f85612c9b9838d9e25c0bd406550071a5867804
            if code_blocks:
                cleaned = code_blocks[-1].strip()
                if cleaned:
                    return cleaned
        return text.strip()

    # ---------- Blocking HTTP POST to MCP ---------- #
    def post_to_mcp(prompt: str, model: str, language: str, endpoint: str = "generate", code: str = None):
        try:
            data = {"prompt": prompt, "model": model, "language": language}
            if code:
                data["code"] = code

            resp = requests.post(
                f"http://localhost:3000/{endpoint}",
                json=data,
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"MCP request failed: {str(e)}", type_="ERROR")
            return {"error": f"MCP error: {e}"}

    # ---------- Command: Generate Code ---------- #
    @bot.command(
        name="gencode",
        description="Generate code using MCP + OpenRouter",
        usage="--model <model> --lang <language> <prompt>"
    )
    async def gencode(ctx, *, args: str):
        await ctx.message.delete()
        parts = args.split()
        model = "meta-llama/llama-4-maverick:free"
        language = "python"

        # parse flags
        if "--model" in parts:
            idx = parts.index("--model")
            if idx + 1 < len(parts):
                model = parts[idx + 1]
                del parts[idx:idx + 2]
        if "--lang" in parts:
            idx = parts.index("--lang")
            if idx + 1 < len(parts):
                language = parts[idx + 1]
                del parts[idx:idx + 2]

        prompt = " ".join(parts).strip()
        if not prompt:
            await ctx.send("Prompt missing.")
            return

        # read context file (if present)
        context_path = Path(getScriptsPath()) / "project-context" / "prompt-v3.md"
        if context_path.exists():
            context_text = context_path.read_text(encoding="utf-8")
            prompt_full = f"{prompt}\n\n[CONTEXT]\n{context_text}"
        else:
            prompt_full = prompt

        # call MCP asynchronously
        response = await run_in_thread(post_to_mcp, prompt_full, model, language)
        
        if "error" in response:
            await ctx.send(f"Error: {response['error']}")
            return

        # Extract the clean code from the response
        output = clean_response(response["output"])
        version = response.get("version", 1)
        script_name = response.get("scriptName", "unnamed_script")
        
        print(f"Saved as {script_name}_v{version}", type_="INFO")

        # Discord has a 2000 character limit per message
        # We'll use 1900 to be safe and account for the code block markers
        if len(output) < 1900:
            # Format the output properly for Discord
            await ctx.send(f"```{language}\n{output}```\nVersion: {script_name}_v{version}")
        else:
            # For longer outputs, save as a file
            temp = Path(getScriptsPath()) / f"{script_name}_v{version}.py"
            temp.write_text(output, encoding="utf-8")
            print(f"Saved output to {temp}", type_="INFO")
            await ctx.send(f"Version: {script_name}_v{version}", file=discord.File(str(temp)))
            # Clean up the temporary file
            temp.unlink()

    # ---------- Command: Fix Code ---------- #
    @bot.command(
        name="fixcode",
        description="Fix and improve existing code using MCP + OpenRouter",
        usage="--model <model> --lang <language> <prompt>"
    )
    async def fixcode(ctx, *, args: str):
        await ctx.message.delete()
        parts = args.split()
        model = "meta-llama/llama-4-maverick:free"
        language = "python"

        # parse flags
        if "--model" in parts:
            idx = parts.index("--model")
            if idx + 1 < len(parts):
                model = parts[idx + 1]
                del parts[idx:idx + 2]
        if "--lang" in parts:
            idx = parts.index("--lang")
            if idx + 1 < len(parts):
                language = parts[idx + 1]
                del parts[idx:idx + 2]

        prompt = " ".join(parts).strip()
        if not prompt:
            await ctx.send("Prompt missing.")
            return

        # Get the latest version's code
        versions_dir = Path(getScriptsPath()) / "versions"
        versions_file = versions_dir / "versions.json"
        if not versions_file.exists():
            await ctx.send("No versions found. Use gencode first.")
            return

        # Read versions file to get script names
        with open(versions_file, 'r') as f:
            versions = json.load(f)

        if not versions:
            await ctx.send("No versions found. Use gencode first.")
            return

        # Get the most recent script and version
        latest_script = None
        latest_version = 0
        for script_name, script_versions in versions.items():
            script_latest = max(int(v) for v in script_versions.keys())
            if script_latest > latest_version:
                latest_version = script_latest
                latest_script = script_name

        if not latest_script:
            await ctx.send("No previous version found. Use gencode first.")
            return

        # Read the latest version's code
        versions_dir = Path(getScriptsPath()) / "versions"
        latest_file = versions_dir / f"{latest_script}_v{latest_version}.py"
        
        print(f"[DEBUG] Looking for file: {latest_file}")
        if not latest_file.exists():
            await ctx.send(f"Version {latest_script}_v{latest_version} file not found.")
            return

        code = latest_file.read_text(encoding="utf-8")

        # call MCP asynchronously
        response = await run_in_thread(post_to_mcp, prompt, model, language, "fixcode", code)
        
        if "error" in response:
            await ctx.send(f"Error: {response['error']}")
            return

        # Extract the clean code from the response
        output = clean_response(response["output"])
        version = response.get("version", latest_version + 1)
        script_name = response.get("scriptName", latest_script)
        
        print(f"Saved as {script_name}_v{version}", type_="INFO")

        # Discord has a 2000 character limit per message
        # We'll use 1900 to be safe and account for the code block markers
        if len(output) < 1900:
            # Format the output properly for Discord
            await ctx.send(f"```{language}\n{output}```\nVersion: {script_name}_v{version}")
        else:
            # For longer outputs, save as a file
            temp = Path(getScriptsPath()) / f"{script_name}_v{version}.py"
            temp.write_text(output, encoding="utf-8")
            print(f"Saved output to {temp}", type_="INFO")
            await ctx.send(f"Version: {script_name}_v{version}", file=discord.File(str(temp)))
            # Clean up the temporary file
            temp.unlink()


# ---- Initialize script ---- #
generate_code_script()
