import asyncio
import datetime
import re
import shlex

@nightyScript(
    name="Channel Importer",
    author="thedorekaczynski",
    description="Importa mensajes de un canal a otro con opciones de filtrado y reemplazo.",
    usage="<p>importmsgs --source <src_id> --dest <dest_id> [--limit <n>] [--skip word1,word2] [--replace old=new,...] [--remove-lines 1,2] [--omit-lines-with w1,w2] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--include-files] [--signature text]"
)
def channel_importer():
    """
    CHANNEL IMPORTER
    ----------------
    Copia mensajes de un canal de Discord a otro con filtros personalizables.

    COMMANDS:
        <p>importmsgs --source <src_id> --dest <dest_id> [--limit <n>] [--skip w1,w2] [--replace old=new] [--remove-lines 1,2] [--omit-lines-with w1,w2] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--include-files] [--signature text]
            --source <src_id>      ID del canal origen.
            --dest <dest_id>       ID del canal destino.
            --limit <n>           Cantidad de mensajes a copiar (por defecto 50).
            --skip w1,w2          Omitir mensajes que contengan alguna de estas palabras.
            --replace old=new     Lista de pares para reemplazar palabras.
            --remove-lines 1,2    Elimina las líneas indicadas de cada mensaje antes de enviarlo.
            --omit-lines-with w1,w2 Elimina cualquier línea que contenga alguna de estas palabras.
            --after YYYY-MM-DD    Copiar mensajes posteriores a esta fecha.
            --before YYYY-MM-DD   Copiar mensajes anteriores a esta fecha.
            --include-files       Adjuntar también los archivos de cada mensaje.
            --signature text      Añadir esta firma al final de cada mensaje copiado.

    EXAMPLES:
        <p>importmsgs --source 123 --dest 456 --skip spam --replace hola=hi --include-files
        <p>importmsgs --source 111 --dest 222 --limit 20 --remove-lines 1 --after 2024-01-01 --signature "Copiado"

    NOTES:
    - Utiliza métodos asíncronos de Nighty para acceder al historial de mensajes.
    - Si se especifica --include-files también copiará adjuntos.
    """

    import shlex  # ensure availability in Nighty's runtime

    def parse_replacements(value: str):
        repl = {}
        for pair in value.split(','):
            if '=' in pair:
                old, new = pair.split('=', 1)
                repl[old] = new
        return repl

    def remove_specified_lines(content: str, lines):
        if not lines:
            return content
        parts = content.split('\n')
        filtered = [line for idx, line in enumerate(parts, start=1) if idx not in lines]
        return '\n'.join(filtered)

    def remove_lines_with_words(content: str, words):
        if not words:
            return content
        lines = content.split('\n')
        filtered = []
        for line in lines:
            lower = line.lower()
            if any(word.lower() in lower for word in words):
                continue
            filtered.append(line)
        return '\n'.join(filtered)

    def parse_date(value: str):
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None

    @bot.command(
        name="importmsgs",
        description="Importa mensajes de un canal a otro con filtros opcionales.",
        usage="--source <src_id> --dest <dest_id> [--limit <n>] [--skip w1,w2] [--replace old=new] [--remove-lines 1,2] [--omit-lines-with w1,w2] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--include-files] [--signature text]"
    )
    async def importmsgs(ctx, *, args: str):
        await ctx.message.delete()
        parts = shlex.split(args)
        source_id = None
        dest_id = None
        limit = 50
        skip_words = []
        replacements = {}
        remove_lines = []
        omit_words = []
        after_date = None
        before_date = None
        include_files = False
        signature = ""

        def consume_option(opt: str):
            if opt in parts:
                idx = parts.index(opt)
                if idx + 1 < len(parts):
                    value = parts[idx + 1]
                    del parts[idx:idx + 2]
                    return value
            return None

        src_val = consume_option('--source')
        dst_val = consume_option('--dest')
        lim_val = consume_option('--limit')
        skip_val = consume_option('--skip')
        replace_val = consume_option('--replace')
        rm_lines_val = consume_option('--remove-lines')
        omit_words_val = consume_option('--omit-lines-with')
        after_val = consume_option('--after')
        before_val = consume_option('--before')
        sig_val = consume_option('--signature')
        if '--include-files' in parts:
            include_files = True
            parts.remove('--include-files')

        if src_val:
            try:
                source_id = int(src_val)
            except ValueError:
                await ctx.send("ID de canal origen inválido.")
                return
        if dst_val:
            try:
                dest_id = int(dst_val)
            except ValueError:
                await ctx.send("ID de canal destino inválido.")
                return
        if lim_val:
            try:
                limit = int(lim_val)
            except ValueError:
                await ctx.send("Valor de --limit inválido.")
                return
        if skip_val:
            skip_words = [w.strip() for w in skip_val.split(',') if w.strip()]
        if replace_val:
            replacements = parse_replacements(replace_val)
        if rm_lines_val:
            try:
                remove_lines = [int(n) for n in rm_lines_val.split(',') if n.isdigit()]
            except ValueError:
                await ctx.send("Líneas inválidas en --remove-lines.")
                return
        if omit_words_val:
            omit_words = [w.strip() for w in omit_words_val.split(',') if w.strip()]
        if after_val:
            after_date = parse_date(after_val)
            if after_date is None:
                await ctx.send("Formato de fecha inválido en --after (YYYY-MM-DD).")
                return
        if before_val:
            before_date = parse_date(before_val)
            if before_date is None:
                await ctx.send("Formato de fecha inválido en --before (YYYY-MM-DD).")
                return
        if sig_val:
            signature = sig_val

        if source_id is None or dest_id is None:
            await ctx.send("Debes especificar --source y --dest.")
            return

        src_channel = bot.get_channel(source_id)
        dst_channel = bot.get_channel(dest_id)
        if not src_channel or not dst_channel:
            await ctx.send("No pude acceder a uno de los canales.")
            return

        try:
            msgs = []
            async for msg in src_channel.history(limit=limit, oldest_first=True, after=after_date, before=before_date):
                text = msg.content
                if any(word.lower() in text.lower() for word in skip_words):
                    continue
                text = remove_specified_lines(text, remove_lines)
                text = remove_lines_with_words(text, omit_words)
                for old, new in replacements.items():
                    text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
                if signature:
                    text = f"{text}\n{signature}" if text else signature
                files = []
                if include_files:
                    for att in msg.attachments:
                        try:
                            files.append(await att.to_file())
                        except Exception as e:
                            print(f"Error leyendo adjunto: {e}", type_="ERROR")
                msgs.append((text, files))
        except Exception as e:
            await ctx.send(f"Error obteniendo mensajes: {e}")
            return

        for content, files in msgs:
            if content or files:
                try:
                    if files:
                        await dst_channel.send(content or "", files=files)
                    else:
                        await dst_channel.send(content)
                except Exception as e:
                    print(f"Error enviando mensaje: {e}", type_="ERROR")
                    await asyncio.sleep(1)

channel_importer()
