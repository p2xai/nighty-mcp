from pathlib import Path
import requests               # synchronous HTTP client
import asyncio
import discord
import re


@nightyScript(
    name="Generate Code",
    author="thedorekaczynski", 
    description="Generate source‑code by sending a prompt and project docs to a local MCP server (OpenRouter backend).",
    usage="<p>gencode --model <model> --lang <language> <prompt>"
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

    EXAMPLES:
        <p>gencode build a simple flask api
        <p>gencode --model gpt-4 --lang js build a websocket server

    NOTES:
    - Uses *requests* wrapped with run_in_thread to avoid blocking Nighty's event loop.
    - Reads context from scripts/project-context/prompt-v3.md each time.
    - Output <1 900 chars returned as fenced block; else attached as file.
    """

    # ---------- Helper: run blocking IO in a thread ---------- #
    async def run_in_thread(func, *args, **kwargs):
        """Run sync function in a thread to keep the loop free."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    # ---------- Helper: clean up response ---------- #
    def clean_response(text: str) -> str:
        """Clean up the response by removing explanatory text and fixing code blocks."""
        # Remove any explanatory text after the code block
        if "```" in text:
            # Find the last code block
            code_blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
            if code_blocks:
                return code_blocks[-1].strip()
        return text.strip()

    # ---------- Blocking HTTP POST to MCP ---------- #
    def post_to_mcp(prompt: str, model: str, language: str):
        try:
            resp = requests.post(
                "http://localhost:3000/generate",
                json={"prompt": prompt, "model": model, "language": language},
                timeout=30
            )
            resp.raise_for_status()
            output = resp.json().get("output", "[no output]")
            return clean_response(output)
        except Exception as e:
            return f"MCP error: {e}"

    # ---------- Command ---------- #
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
        output = await run_in_thread(post_to_mcp, prompt_full, model, language)
        
        # Log output details
        print(f"Output length: {len(output)} characters", type_="INFO")

        # Discord has a 2000 character limit per message
        # We'll use 1900 to be safe and account for the code block markers
        if len(output) < 1900:
            await ctx.send(f"```{language}\n{output}```")
        else:
            # For longer outputs, save as a file
            temp = Path(getScriptsPath()) / "generated.py"
            temp.write_text(output, encoding="utf-8")
            print(f"Saved output to {temp} ({len(output)} characters)", type_="INFO")
            await ctx.send(file=discord.File(str(temp)))
            # Clean up the temporary file
            temp.unlink()


# ---- Initialize script ---- #
generate_code_script()
