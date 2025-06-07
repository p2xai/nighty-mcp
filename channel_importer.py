# -*- coding: utf-8 -*-
"""Discord channel import utilities."""

from pathlib import Path
import sys
import asyncio
from datetime import datetime
import json
import os
import re
import shlex
import builtins

# Ensure this script's directory is on sys.path so sibling modules load
# correctly when executed from elsewhere.
_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

# store formatter module in builtins so nested callbacks always find it
product_formatter = getattr(builtins, 'product_formatter', None)
if product_formatter is None:
    try:
        import product_formatter as _pf
        product_formatter = _pf
    except Exception:  # pragma: no cover - safe fallback if anything goes wrong
        product_formatter = False
    builtins.product_formatter = product_formatter

@nightyScript(
    name="Channel Importer",
    author="thedorekaczynski",
    description="Importa mensajes de un canal a otro con opciones de filtrado y reemplazo.",
    usage="<p>importmsgs --source <src_id> --dest <dest_id> [--limit <n>] [--skip word1,word2] [--replace old=new,...] [--remove-lines 1,2] [--omit-lines-with w1,w2] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--include-files] [--signature text] [--mention-role id1,id2] [--format-product]"
)
def channel_importer():
    """
    CHANNEL IMPORTER
    ----------------
    Copia mensajes de un canal de Discord a otro con filtros personalizables.

    COMMANDS:
        <p>importmsgs --source <src_id> --dest <dest_id> [--limit <n>] [--skip w1,w2] [--replace old=new] [--remove-lines 1,2] [--omit-lines-with w1,w2] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--include-files] [--signature text] [--format-product]
        <p>importmsgs stop
        <p>scheduleimport --source <src_id> --dest <dest_id> [opciones] [--interval h] [--format-product]
        <p>stopimport [--source <src_id> --dest <dest_id>]
        <p>status
        <p>rolepost --channel <id> --role <role_id> --emoji 🙂 [--role id2 --emoji :grinning: ...] --text "mensaje"
        <p>delrolepost --message <msg_id> [--channel <id>]
        <p>loadrolepost --message <msg_id> [--channel <id>]
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
            --mention-role id1,id2 Menciona estos roles al enviar cada mensaje importado.
            --format-product      Formatear cada mensaje como producto.
    - Puedes ejecutar `scheduleimport` varias veces para programar importaciones de distintos canales simultáneamente. Usa `stopimport` con los IDs para cancelar una en particular o sin argumentos para detenerlas todas.

    EXAMPLES:
        <p>importmsgs --source 123 --dest 456 --skip spam --replace hola=hi --include-files
        <p>importmsgs --source 111 --dest 222 --limit 20 --remove-lines 1 --after 2024-01-01 --signature "Copiado"
        .importmsgs --source 1162281353216262154 --dest 1379868551367757935 --replace Goshippro=Hause --remove-lines 8 --limit 1 --include-files
        <p>importmsgs --source 321 --dest 654 --format-product
        <p>scheduleimport --source 123 --dest 456 --interval 24 --include-files
        <p>scheduleimport --source 999 --dest 888 --format-product
        <p>importmsgs stop
        <p>rolepost --channel 123 --role 789 --emoji 👍 --role 1011 --emoji 🔥 --text "Acepta las reglas"
        <p>loadrolepost --message 123456789012345678

    NOTES:
    - Utiliza métodos asíncronos de Nighty para acceder al historial de mensajes.
    - Si se especifica --include-files también copiará adjuntos.
    - Se añade automáticamente la línea "Tendencia [fecha]" al final de cada mensaje importado.
    - Con --mention-role se notificará a los roles indicados en cada copia.
    - El comando `rolepost` crea un mensaje de reacción que asigna roles. Puedes indicar varias
      parejas `--role ID --emoji 😀` para ofrecer diferentes roles en un mismo mensaje.
    - Los emojis pueden escribirse directamente o usando el formato `:nombre:`
      (por ejemplo `:smile:`), que el script convertirá automáticamente.
    - Con `delrolepost` puedes borrar un rolepost por ID para que no aparezca en `status`, pero se mantiene almacenado.
    - Los roleposts se guardan en un archivo JSON para poder restaurarlos luego con `loadrolepost`.
    - Las fechas de última importación se guardan en `import_history.json` para reanudar desde el último mensaje tras reiniciar el bot.
    """

    try:
        import emoji as emoji_lib
    except Exception:
        emoji_lib = None
    import shlex

    # almacenamiento de importaciones programadas
    # { (src_id, dest_id): {"task": asyncio.Task, "last_time": datetime|None} }
    scheduled_jobs = {}
    IMPORT_HISTORY_FILE = 'import_history.json'
    if os.path.exists(IMPORT_HISTORY_FILE):
        try:
            with open(IMPORT_HISTORY_FILE, 'r', encoding='utf-8') as fp:
                raw = json.load(fp)
            import_history = {}
            for k, v in raw.items():
                try:
                    s, d = k.split('>')
                    import_history[(int(s), int(d))] = datetime.fromisoformat(v)
                except Exception:
                    pass
        except Exception:
            import_history = {}
    else:
        import_history = {}
    # roleposts activos {message_id: {"channel_id": int, "pairs": [{"role_id": int, "emoji": str}]}}
    reaction_roles = {}
    # almacenamiento persistente de roleposts {id: {channel_id, pairs, active}}
    ROLEPOSTS_FILE = 'roleposts.json'
    if os.path.exists(ROLEPOSTS_FILE):
        try:
            with open(ROLEPOSTS_FILE, 'r', encoding='utf-8') as fp:
                rolepost_store = {int(k): v for k, v in json.load(fp).items()}
        except Exception:
            rolepost_store = {}
    else:
        rolepost_store = {}

    for mid, data in rolepost_store.items():
        if data.get('active'):
            reaction_roles[mid] = {
                'channel_id': data['channel_id'],
                'pairs': data['pairs'],
            }

    def save_roleposts():
        try:
            with open(ROLEPOSTS_FILE, 'w', encoding='utf-8') as fp:
                json.dump(rolepost_store, fp)
        except Exception:
            pass

    def save_import_history():
        try:
            with open(IMPORT_HISTORY_FILE, 'w', encoding='utf-8') as fp:
                data = {f"{k[0]}>{k[1]}": v.isoformat() for k, v in import_history.items()}
                json.dump(data, fp)
        except Exception:
            pass

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
        mention_roles = []
        format_product = False
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
        mention_roles_val = consume_option('--mention-role')
        after_val = consume_option('--after')
        before_val = consume_option('--before')
        sig_val = consume_option('--signature')
        if '--format-product' in parts:
            format_product = True
            parts.remove('--format-product')
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
        if mention_roles_val:
            try:
                mention_roles = [int(r) for r in mention_roles_val.split(',') if r.strip()]
            except ValueError:
                error = "IDs inválidos en --mention-role."
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
            'mention_roles': mention_roles,
            'format_product': format_product,
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
            latest_time = None
            async for msg in src_channel.history(limit=opts['limit'], oldest_first=True, after=opts['after_date'], before=opts['before_date']):
                text = msg.content
                if any(word.lower() in text.lower() for word in opts['skip_words']):
                    continue
                text = remove_specified_lines(text, opts['remove_lines'])
                text = remove_lines_with_words(text, opts['omit_words'])
                for old, new in opts['replacements'].items():
                    text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
                pf = getattr(builtins, 'product_formatter', None)
                if opts.get('format_product'):
                    if pf is None:
                        try:
                            import importlib
                            pf = importlib.import_module('product_formatter')
                            builtins.product_formatter = pf
                        except Exception:
                            pf = False
                            builtins.product_formatter = False
                    if pf and hasattr(pf, 'format_description'):
                        text = await pf.format_description(text)
                trend_line = f"Tendencia [{get_message_date(msg)}]"
                if opts['signature']:
                    text = f"{text}\n{opts['signature']}" if text else opts['signature']
                text = f"{text}\n{trend_line}" if text else trend_line
                if opts['mention_roles']:
                    mentions = ' '.join(f'<@&{rid}>' for rid in opts['mention_roles'])
                    text = f"{mentions}\n{text}" if text else mentions
                files = []
                if opts['include_files']:
                    for att in msg.attachments:
                        try:
                            files.append(await att.to_file())
                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            print(f"Error leyendo adjunto: {e}", type_="ERROR")
                msgs.append((text, files))
                if latest_time is None or msg.created_at > latest_time:
                    latest_time = msg.created_at
        except asyncio.CancelledError:
            raise
        except Exception as e:
            if ctx:
                await ctx.send(f"Error obteniendo mensajes: {e}")
            else:
                print(f"Error obteniendo mensajes: {e}")
            return None

        for content, files in msgs:
            if content or files:
                try:
                    if files:
                        await dst_channel.send(content or "", files=files)
                    else:
                        await dst_channel.send(content)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"Error enviando mensaje: {e}", type_="ERROR")
                    await asyncio.sleep(1)

        if latest_time:
            import_history[(opts['source_id'], opts['dest_id'])] = latest_time
            save_import_history()
        return latest_time



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

    def normalize_emoji(val: str):
        if emoji_lib and val.startswith(':') and val.endswith(':'):
            try:
                return emoji_lib.emojize(val, language='alias')
            except Exception:
                return val
        return val

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
        usage="--source <src_id> --dest <dest_id> [--limit <n>] [--skip w1,w2] [--replace old=new] [--remove-lines 1,2] [--omit-lines-with w1,w2] [--after YYYY-MM-DD] [--before YYYY-MM-DD] [--include-files] [--signature text] [--mention-role id1,id2] [--format-product]"
    )
    async def importmsgs(ctx, *, args: str):
        await ctx.message.delete()
        if args.strip() == "stop":
            if scheduled_jobs:
                for data in scheduled_jobs.values():
                    data['task'].cancel()
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
        usage="--source <src_id> --dest <dest_id> [opciones] [--interval h] [--format-product]"
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
            scheduled_jobs[key]['task'].cancel()
        job_opts = opts.copy()
        if not job_opts.get('after_date'):
            stored = import_history.get(key)
            if stored:
                job_opts['after_date'] = stored

        async def loop_job():
            while True:
                new_time = await do_import(job_opts)
                if new_time:
                    scheduled_jobs[key]['last_time'] = new_time
                    job_opts['after_date'] = new_time
                await asyncio.sleep(interval * 3600)

        task = asyncio.create_task(loop_job())
        scheduled_jobs[key] = {
            "task": task,
            "last_time": job_opts.get('after_date')
        }
        await ctx.send(
            f"Importación programada cada {interval}h para {key[0]} -> {key[1]}."
        )

    @bot.command(
        name="rolepost",
        description="Publica un mensaje con reacciones que otorgan roles",
        usage="--channel <id> --role <id> --emoji <emoji> [--role id2 --emoji e2 ...] --text \"mensaje\""
    )
    async def rolepost(ctx, *, args: str):
        await ctx.message.delete()
        parts = shlex.split(args)

        def consume(opt):
            if opt in parts:
                idx = parts.index(opt)
                if idx + 1 < len(parts):
                    val = parts[idx + 1]
                    del parts[idx:idx + 2]
                    return val
            return None

        ch_val = consume('--channel')
        text_val = consume('--text')

        roles = []
        emojis = []
        while '--role' in parts and '--emoji' in parts:
            r_val = consume('--role')
            e_val = consume('--emoji')
            if not r_val or not e_val:
                break
            try:
                roles.append(int(r_val))
            except ValueError:
                await ctx.send("ID de rol inválido.")
                return
            emojis.append(normalize_emoji(e_val))

        if not roles or len(roles) != len(emojis):
            await ctx.send("Debes especificar pares de --role y --emoji.")
            return

        channel = bot.get_channel(int(ch_val)) if ch_val else ctx.channel
        if not channel:
            await ctx.send("Canal inválido.")
            return

        message = await channel.send(text_val or "Reacciona para obtener roles")
        for emoji_val in emojis:
            try:
                await message.add_reaction(emoji_val)
                await asyncio.sleep(0.3)
            except asyncio.CancelledError:
                raise
            except Exception:
                await ctx.send("No pude añadir la reacción.")
        reaction_roles[message.id] = {
            "channel_id": channel.id,
            "pairs": [
                {"role_id": rid, "emoji": str(em)} for rid, em in zip(roles, emojis)
            ],
        }
        rolepost_store[message.id] = {
            "channel_id": channel.id,
            "pairs": [
                {"role_id": rid, "emoji": str(em)} for rid, em in zip(roles, emojis)
            ],
            "active": True,
        }
        save_roleposts()
        await ctx.send("Mensaje creado.")

    @bot.command(
        name="delrolepost",
        description="Elimina un rolepost existente",
        usage="--message <id> [--channel <chan_id>]",
    )
    async def delrolepost(ctx, *, args: str):
        await ctx.message.delete()
        parts = shlex.split(args)

        def consume(opt):
            if opt in parts:
                idx = parts.index(opt)
                if idx + 1 < len(parts):
                    val = parts[idx + 1]
                    del parts[idx:idx + 2]
                    return val
            return None

        msg_val = consume('--message')
        ch_val = consume('--channel')
        if not msg_val:
            await ctx.send('Debes especificar --message <id>.')
            return
        try:
            msg_id = int(msg_val)
        except ValueError:
            await ctx.send('ID de mensaje inválido.')
            return

        data = reaction_roles.pop(msg_id, None)
        if not data and msg_id not in rolepost_store:
            await ctx.send('No existe un rolepost con ese ID.')
            return
        if data is None:
            data = rolepost_store.get(msg_id)
        if msg_id in rolepost_store:
            rolepost_store[msg_id]['active'] = False
        else:
            rolepost_store[msg_id] = {
                'channel_id': data.get('channel_id'),
                'pairs': data.get('pairs', []),
                'active': False,
            }
        save_roleposts()
        
        # intentar borrar el mensaje
        channel = None
        if ch_val:
            try:
                channel = bot.get_channel(int(ch_val))
            except Exception:
                channel = None
        if not channel:
            ch_id = data.get('channel_id')
            channel = bot.get_channel(ch_id) if ch_id else None
        if channel:
            try:
                msg = await channel.fetch_message(msg_id)
                await msg.delete()
            except asyncio.CancelledError:
                raise
            except Exception:
                pass
        await ctx.send(f"Rolepost {msg_id} eliminado.")

    @bot.command(
        name="loadrolepost",
        description="Recarga un rolepost almacenado",
        usage="--message <id> [--channel <chan_id>]",
    )
    async def loadrolepost(ctx, *, args: str):
        await ctx.message.delete()
        parts = shlex.split(args)

        def consume(opt):
            if opt in parts:
                idx = parts.index(opt)
                if idx + 1 < len(parts):
                    val = parts[idx + 1]
                    del parts[idx:idx + 2]
                    return val
            return None

        msg_val = consume('--message')
        ch_val = consume('--channel')
        if not msg_val:
            await ctx.send('Debes especificar --message <id>.')
            return
        try:
            msg_id = int(msg_val)
        except ValueError:
            await ctx.send('ID de mensaje inválido.')
            return

        data = rolepost_store.get(msg_id)
        if not data:
            await ctx.send('No existe un rolepost almacenado con ese ID.')
            return

        channel = None
        if ch_val:
            try:
                channel = bot.get_channel(int(ch_val))
            except Exception:
                channel = None
        if not channel:
            channel = bot.get_channel(data.get('channel_id'))
        if not channel:
            await ctx.send('Canal inválido.')
            return

        try:
            await channel.fetch_message(msg_id)
        except Exception:
            await ctx.send('No se encontró el mensaje.')
            return

        reaction_roles[msg_id] = {
            'channel_id': channel.id,
            'pairs': data['pairs'],
        }
        rolepost_store[msg_id]['active'] = True
        save_roleposts()
        await ctx.send(f"Rolepost {msg_id} cargado.")

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
            data = scheduled_jobs.pop(key, None)
            if data:
                data['task'].cancel()
                await ctx.send(f"Importación {src}->{dst} detenida.")
            else:
                await ctx.send("No existe importación programada para esos canales.")
        else:
            for data in scheduled_jobs.values():
                data['task'].cancel()
            scheduled_jobs.clear()
            await ctx.send("Todas las importaciones programadas fueron detenidas.")

    @bot.command(
        name="status",
        description="Muestra las importaciones programadas y los roleposts activos.",
        usage=""
    )
    async def status(ctx):
        await ctx.message.delete()
        lines = []
        if scheduled_jobs:
            lines.append("Importaciones programadas:")
            for (src, dst), data in scheduled_jobs.items():
                lt = data.get('last_time')
                if isinstance(lt, datetime):
                    ts = lt.strftime('%Y-%m-%d %H:%M')
                    lines.append(f"- {src} -> {dst} (última: {ts})")
                else:
                    lines.append(f"- {src} -> {dst}")
        else:
            lines.append("No hay importaciones programadas.")
        if import_history:
            lines.append("Historial de importaciones:")
            for (src, dst), ts in import_history.items():
                if isinstance(ts, datetime):
                    ts_str = ts.strftime('%Y-%m-%d %H:%M')
                else:
                    ts_str = str(ts)
                lines.append(f"- {src} -> {dst}: {ts_str}")
        if reaction_roles:
            lines.append("Roleposts activos:")
            for mid, data in reaction_roles.items():
                pairs = data['pairs']
                info = ', '.join(f"{p['emoji']}→{p['role_id']}" for p in pairs)
                lines.append(f"- mensaje {mid}: {info}")
        else:
            lines.append("No hay roleposts activos.")
        inactive = {m: d for m, d in rolepost_store.items() if not d.get('active')}
        if inactive:
            lines.append("Roleposts almacenados:")
            for mid, data in inactive.items():
                pairs = data['pairs']
                info = ', '.join(f"{p['emoji']}→{p['role_id']}" for p in pairs)
                lines.append(f"- mensaje {mid}: {info}")
        await ctx.send('\n'.join(lines))

    @bot.event
    async def on_raw_reaction_add(payload):
        data = reaction_roles.get(payload.message_id)
        if not data or not payload.guild_id:
            return
        pairs = data['pairs']
        pair = None
        emoji_val = normalize_emoji(str(payload.emoji))
        for p in pairs:
            if emoji_val == p["emoji"]:
                pair = p
                break
        if not pair:
            return
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(pair["role_id"])
        if member and role:
            await member.add_roles(role)

    @bot.event
    async def on_raw_reaction_remove(payload):
        data = reaction_roles.get(payload.message_id)
        if not data or not payload.guild_id:
            return
        pairs = data['pairs']
        pair = None
        emoji_val = normalize_emoji(str(payload.emoji))
        for p in pairs:
            if emoji_val == p["emoji"]:
                pair = p
                break
        if not pair:
            return
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(pair["role_id"])
        if member and role:
            await member.remove_roles(role)

channel_importer()