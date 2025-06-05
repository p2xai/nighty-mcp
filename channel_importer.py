import asyncio
from datetime import datetime
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
        <p>importmsgs stop
        <p>scheduleimport --source <src_id> --dest <dest_id> [opciones] [--interval h]
        <p>stopimport [--source <src_id> --dest <dest_id>]
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
    - Puedes ejecutar `scheduleimport` varias veces para programar importaciones de distintos canales simultáneamente. Usa `stopimport` con los IDs para cancelar una en particular o sin argumentos para detenerlas todas.

    EXAMPLES:
        <p>importmsgs --source 123 --dest 456 --skip spam --replace hola=hi --include-files
        <p>importmsgs --source 111 --dest 222 --limit 20 --remove-lines 1 --after 2024-01-01 --signature "Copiado"
        .importmsgs --source 1162281353216262154 --dest 1379868551367757935 --replace Goshippro=Hause --remove-lines 8 --limit 1 --include-files
        <p>scheduleimport --source 123 --dest 456 --interval 24 --include-files
        <p>importmsgs stop

    NOTES:
    - Utiliza métodos asíncronos de Nighty para acceder al historial de mensajes.
    - Si se especifica --include-files también copiará adjuntos.
    - Se añade automáticamente la línea "Tendencia [fecha]" al final de cada mensaje importado.
    """

    import shlex  # ensure availability in Nighty's runtime

    # almacenamiento de importaciones programadas { (src_id, dest_id): Loop }
    scheduled_jobs = {}

    def parse_arguments(parts):
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
        error = None

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
                error = "ID de canal origen inválido."
        if dst_val:
            try:
                dest_id = int(dst_val)
            except ValueError:
                error = "ID de canal destino inválido."
        if lim_val:
            try:
                limit = int(lim_val)
            except ValueError:
                error = "Valor de --limit inválido."
        if skip_val:
            skip_words = [w.strip() for w in skip_val.split(',') if w.strip()]
        if replace_val:
            replacements = parse_replacements(replace_val)
        if rm_lines_val:
            try:
                remove_lines = [int(n) for n in rm_lines_val.split(',') if n.isdigit()]
            except ValueError:
                error = "Líneas inválidas en --remove-lines."
        if omit_words_val:
            omit_words = [w.strip() for w in omit_words_val.split(',') if w.strip()]
        if after_val:
            after_date = parse_date(after_val)
            if after_date is None:
                error = "Formato de fecha inválido en --after (YYYY-MM-DD)."
        if before_val:
            before_date = parse_date(before_val)
            if before_date is None:
                error = "Formato de fecha inválido en --before (YYYY-MM-DD)."
        if sig_val:
            signature = sig_val

        return {
            'source_id': source_id,
            'dest_id': dest_id,
            'limit': limit,
            'skip_words': skip_words,
            'replacements': replacements,
            'remove_lines': remove_lines,
            'omit_words': omit_words,
            'after_date': after_date,
            'before_date': before_date,
            'include_files': include_files,
            'signature': signature,
        }, error

    async def do_import(opts, ctx=None):
        src_channel = bot.get_channel(opts['source_id'])
        dst_channel = bot.get_channel(opts['dest_id'])
        if not src_channel or not dst_channel:
            if ctx:
                await ctx.send("No pude acceder a uno de los canales.")
            return

        try:
            msgs = []
            async for msg in src_channel.history(limit=opts['limit'], oldest_first=True, after=opts['after_date'], before=opts['before_date']):
                text = msg.content
                if any(word.lower() in text.lower() for word in opts['skip_words']):
                    continue
                text = remove_specified_lines(text, opts['remove_lines'])
                text = remove_lines_with_words(text, opts['omit_words'])
                for old, new in opts['replacements'].items():
                    text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
                trend_line = f"Tendencia [{get_message_date(msg)}]"
                if opts['signature']:
                    text = f"{text}\n{opts['signature']}" if text else opts['signature']
                text = f"{text}\n{trend_line}" if text else trend_line
                files = []
                if opts['include_files']:
                    for att in msg.attachments:
                        try:
                            files.append(await att.to_file())
                        except Exception as e:
                            print(f"Error leyendo adjunto: {e}", type_="ERROR")
                msgs.append((text, files))
        except Exception as e:
            if ctx:
                await ctx.send(f"Error obteniendo mensajes: {e}")
            else:
                print(f"Error obteniendo mensajes: {e}")
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
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None

    def get_message_date(msg):
        return msg.created_at.strftime("%Y-%m-%d")

    @bot.command(
        name="importmsgs",
        description="Importa mensajes de un canal a otro con filtros opcionales.",
        usage="--source <src_id> --dest <dest_id> [--limit <n>] [--skip w1,w2] [--replace old=new] [--remove-lines 1,2] [--omit-lines-with w1,w2] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--include-files] [--signature text]"
    )
    async def importmsgs(ctx, *, args: str):
        await ctx.message.delete()
        if args.strip() == "stop":
            if scheduled_jobs:
                for loop in scheduled_jobs.values():
                    loop.cancel()
                scheduled_jobs.clear()
                await ctx.send("Todas las importaciones programadas fueron detenidas.")
            else:
                await ctx.send("No hay importaciones programadas.")
            return
        parts = shlex.split(args)
        opts, error = parse_arguments(parts)
        if error:
            await ctx.send(error)
            return
        if opts['source_id'] is None or opts['dest_id'] is None:
            await ctx.send("Debes especificar --source y --dest.")
            return
        await do_import(opts, ctx)

    @bot.command(
        name="scheduleimport",
        description="Programa la importación periódica de mensajes.",
        usage="--source <src_id> --dest <dest_id> [opciones] [--interval h]"
    )
    async def scheduleimport(ctx, *, args: str):
        await ctx.message.delete()
        parts = shlex.split(args)
        interval = 24
        if '--interval' in parts:
            idx = parts.index('--interval')
            if idx + 1 < len(parts):
                val = parts[idx + 1]
                del parts[idx:idx + 2]
                try:
                    interval = float(val)
                except ValueError:
                    await ctx.send("Valor de --interval inválido.")
                    return
        opts, error = parse_arguments(parts)
        if error:
            await ctx.send(error)
            return
        if opts['source_id'] is None or opts['dest_id'] is None:
            await ctx.send("Debes especificar --source y --dest.")
            return
        key = (opts['source_id'], opts['dest_id'])
        if key in scheduled_jobs:
            scheduled_jobs[key].cancel()
        job_opts = opts.copy()

        async def loop_job():
            while True:
                await do_import(job_opts)
                await asyncio.sleep(interval * 3600)

        task = asyncio.create_task(loop_job())
        scheduled_jobs[key] = task
        await ctx.send(
            f"Importación programada cada {interval}h para {key[0]} -> {key[1]}."
        )

    @bot.command(
        name="stopimport",
        description="Detiene la importación programada.",
        usage="[--source <src_id> --dest <dest_id>]"
    )
    async def stopimport(ctx, *, args: str = ""):
        await ctx.message.delete()
        parts = shlex.split(args)

        def consume_option(opt):
            if opt in parts:
                idx = parts.index(opt)
                if idx + 1 < len(parts):
                    val = parts[idx + 1]
                    del parts[idx:idx + 2]
                    return val
            return None

        src_val = consume_option('--source')
        dst_val = consume_option('--dest')

        if src_val and dst_val:
            try:
                src = int(src_val)
                dst = int(dst_val)
            except ValueError:
                await ctx.send("IDs inválidos.")
                return
            key = (src, dst)
            task = scheduled_jobs.pop(key, None)
            if task:
                task.cancel()
                await ctx.send(f"Importación {src}->{dst} detenida.")
            else:
                await ctx.send("No existe importación programada para esos canales.")
        else:
            for task in scheduled_jobs.values():
                task.cancel()
            scheduled_jobs.clear()
            await ctx.send("Todas las importaciones programadas fueron detenidas.")

channel_importer()
