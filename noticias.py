# -*- coding: utf-8 -*-
import os
import asyncio
from datetime import datetime
import requests
import shlex

@nightyScript(
    name="News Alerts",
    author="thedorekaczynski",
    description="Envía titulares recientes usando NewsAPI y puede programar envíos periódicos.",
    usage="<p>noticias [opciones]"
)
def noticias_script():
    """
    NEWS ALERTS
    -----------
    Obtiene titulares de https://newsapi.org/ y los publica en un canal de Discord.

    COMMANDS:
        <p>noticias [opciones]
            --country <código>     País (es, us, mx, ...)
            --category <nombre>    business, sports, technology, ...
            --query <texto>        Búsqueda por palabras clave
            --limit <n>            Número de artículos (por defecto 5)
            --channel <id>         Canal destino (predeterminado: actual)
            --mention-role <id1,id2>  Menciona estos roles al publicar
        <p>schedulenews [opciones] --interval <h>
        <p>stopnews [--channel <id>]

    EXAMPLES:
        <p>noticias --country es --category technology --limit 3
        <p>schedulenews --query deportes --interval 12 --mention-role 12345
        <p>stopnews --channel 12345

    NOTES:
    - Obtén una API key gratis en https://newsapi.org/ y colócala en la variable de entorno NEWS_API_KEY.
    - Los mensajes incluyen la fecha y título de cada artículo con su URL.
    - Schedulenews permite publicar noticias de forma periódica cada N horas.
    """

    API_KEY = os.getenv("NEWS_API_KEY", "")
    BASE_URL = "https://newsapi.org/v2/top-headlines"

    scheduled_tasks = {}

    async def run_in_thread(func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def fetch_news(opts):
        params = {"apiKey": API_KEY, "pageSize": opts.get("limit", 5)}
        if opts.get("country"):
            params["country"] = opts["country"]
        if opts.get("category"):
            params["category"] = opts["category"]
        if opts.get("query"):
            params["q"] = opts["query"]
        resp = await run_in_thread(requests.get, BASE_URL, params=params, timeout=10)
        data = resp.json()
        return data.get("articles", [])

    async def post_news(channel_id, opts):
        channel = bot.get_channel(channel_id)
        if not channel:
            return
        articles = await fetch_news(opts)
        mention = ""
        roles = opts.get("mention_roles") or []
        if roles:
            mention = " ".join(f"<@&{r}>" for r in roles)
        for art in articles:
            title = art.get("title", "Sin título")
            url = art.get("url", "")
            date = art.get("publishedAt", "")
            try:
                date = datetime.fromisoformat(date.rstrip("Z")).strftime("%Y-%m-%d")
            except Exception:
                date = ""
            header = f"Tendencia [{date}]" if date else "Tendencia"
            text = f"{header}\n**{title}**\n{url}"
            if mention:
                text = f"{mention}\n{text}"
            await channel.send(text)
            await asyncio.sleep(0.3)

    def parse_args(parts):
        opts = {"limit": 5, "mention_roles": []}

        def consume(opt):
            if opt in parts:
                idx = parts.index(opt)
                if idx + 1 < len(parts):
                    val = parts[idx + 1]
                    del parts[idx:idx + 2]
                    return val
            return None

        country = consume("--country")
        category = consume("--category")
        query = consume("--query")
        limit_val = consume("--limit")
        channel_val = consume("--channel")
        roles_val = consume("--mention-role")

        if country:
            opts["country"] = country
        if category:
            opts["category"] = category
        if query:
            opts["query"] = query
        if limit_val:
            try:
                opts["limit"] = int(limit_val)
            except ValueError:
                opts["limit"] = 5
        if channel_val:
            try:
                opts["channel"] = int(channel_val)
            except ValueError:
                pass
        if roles_val:
            try:
                opts["mention_roles"] = [int(r) for r in roles_val.split(',') if r.strip()]
            except ValueError:
                pass
        return opts

    @bot.command(name="noticias", description="Envía titulares de noticias", usage="[opciones]")
    async def noticias_cmd(ctx, *, args: str = ""):
        await ctx.message.delete()
        parts = shlex.split(args)
        opts = parse_args(parts)
        channel_id = opts.pop("channel", ctx.channel.id)
        if not API_KEY:
            await ctx.send("NEWS_API_KEY no configurada.")
            return
        await post_news(channel_id, opts)

    @bot.command(name="schedulenews", description="Programa envíos de noticias", usage="[opciones] --interval <h>")
    async def schedulenews(ctx, *, args: str):
        await ctx.message.delete()
        parts = shlex.split(args)
        interval = 24
        if "--interval" in parts:
            idx = parts.index("--interval")
            if idx + 1 < len(parts):
                val = parts[idx + 1]
                del parts[idx:idx + 2]
                try:
                    interval = float(val)
                except ValueError:
                    await ctx.send("Valor de --interval inválido.")
                    return
        opts = parse_args(parts)
        channel_id = opts.pop("channel", ctx.channel.id)
        if not API_KEY:
            await ctx.send("NEWS_API_KEY no configurada.")
            return
        async def loop_job():
            while True:
                await post_news(channel_id, opts)
                await asyncio.sleep(interval * 3600)
        if channel_id in scheduled_tasks:
            scheduled_tasks[channel_id].cancel()
        task = asyncio.create_task(loop_job())
        scheduled_tasks[channel_id] = task
        await ctx.send(f"Noticias programadas cada {interval}h en {channel_id}.")

    @bot.command(name="stopnews", description="Detiene noticias programadas", usage="[--channel <id>]")
    async def stopnews(ctx, *, args: str = ""):
        await ctx.message.delete()
        parts = shlex.split(args)
        channel_val = None
        if "--channel" in parts:
            idx = parts.index("--channel")
            if idx + 1 < len(parts):
                channel_val = parts[idx + 1]
                del parts[idx:idx + 2]
        ch_id = int(channel_val) if channel_val else ctx.channel.id
        task = scheduled_tasks.pop(ch_id, None)
        if task:
            task.cancel()
            await ctx.send(f"Noticias detenidas en {ch_id}.")
        else:
            await ctx.send("No hay noticias programadas para ese canal.")

noticias_script()
