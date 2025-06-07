# -*- coding: utf-8 -*-
"""Utility to format product descriptions for Discord."""

from pathlib import Path
import sys
import asyncio
import re
import builtins
import types
try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None


# Ensure this script's directory is on sys.path so sibling modules can be
# imported even if executed from another location.
_MODULE_DIR = Path(__file__).resolve().parent
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

# Provide no-op defaults when running outside Nighty
if not hasattr(builtins, "nightyScript"):
    builtins.nightyScript = lambda *a, **k: (lambda f: f)
if not hasattr(builtins, "bot"):
    builtins.bot = types.SimpleNamespace(command=lambda *a, **k: (lambda f: f))

@nightyScript(
    name="Product Formatter",
    author="thedorekaczynski",
    description="Format product info and categorize with OpenRouter",
    usage="<p>formatproduct <raw description>"
)
def product_formatter():
    """
    PRODUCT FORMATTER
    -----------------
    Takes a raw product description string, strips date patterns and
    removes trailing "Keyword..." sections,
    extracts price and shipping per country, categorizes the product title
    via the local MCP server (OpenRouter backend) and returns a nicely
    formatted Discord message with flag emojis.

    COMMANDS:
        <p>formatproduct <raw description>

    EXAMPLES:
        <p>formatproduct USA $99 shipping $10, UK £80 shipping £5 - Super Widget 2024-06-30
        <p>formatproduct USA $99 shipping $10, UK £80 shipping £5 - Super Widget 2024-06-30 Keyword: gadget sale
            **Super Widget**
            _Category: Example_
            \U0001F1FA\U0001F1F8 $99 + $10 shipping
            \U0001F1EC\U0001F1E7 £80 + £5 shipping

    NOTES:
    - Dates in the form YYYY-MM-DD or YYYY/MM/DD are removed from the input.
    - Any trailing text beginning with "Keyword" (case-insensitive) is stripped.
    """

    async def run_in_thread(func, *args, **kwargs):
        """Run sync function in thread."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    def clean_block(text: str) -> str:
        m = re.search(r"```(?:text)?\n(.*?)```", text, re.DOTALL)
        return m.group(1).strip() if m else text.strip()

    def call_mcp(prompt: str, model: str = "meta-llama/llama-4-maverick:free") -> str:
        if requests is None:
            return "Unknown (requests library not installed)"
        try:
            resp = requests.post(
                "http://localhost:3000/generate",
                json={"prompt": prompt, "model": model, "language": "text"},
                timeout=30,
            )
            resp.raise_for_status()
            return clean_block(resp.json().get("output", ""))
        except Exception as e:
            return f"Unknown ({e})"

    FLAG_MAP = {
        "USA": "\U0001F1FA\U0001F1F8",
        "US": "\U0001F1FA\U0001F1F8",
        "UK": "\U0001F1EC\U0001F1E7",
        "GB": "\U0001F1EC\U0001F1E7",
        "DE": "\U0001F1E9\U0001F1EA",
        "AU": "\U0001F1E6\U0001F1FA",
        "CA": "\U0001F1E8\U0001F1E6",
        "FR": "\U0001F1EB\U0001F1F7",
        "IT": "\U0001F1EE\U0001F1F9",
        "ES": "\U0001F1EA\U0001F1F8",
        "JP": "\U0001F1EF\U0001F1F5"
    }

    def parse_prices(text: str):
        """Extract price + shipping info per country from the raw text."""
        data = {}

        # first split by common separators like newlines, commas or semicolons
        for part in re.split(r"[\n,;]+", text):
            part = part.strip()
            if not part:
                continue

            # each part may contain multiple country/price pairs separated by '/'
            for sub in part.split('/'):
                sub = sub.strip()
                if not sub:
                    continue
                if re.search(r"\bdays?\b", sub, re.I):
                    continue

                # format 1: "USA $99" (optionally with "shipping $X")
                m1 = re.match(r"^\b([A-Za-z]{2,3})\b[^$€£\d]*([$€£]?\d+(?:\.\d+)?)", sub)
                if m1:
                    code = m1.group(1).upper()
                    price = m1.group(2)
                else:
                    # format 2: "$99 to USA"
                    m2 = re.match(r"([$€£]?\d+(?:\.\d+)?)\s*to\s*([A-Za-z]{2,3})", sub, re.I)
                    if not m2:
                        continue
                    price = m2.group(1)
                    code = m2.group(2).upper()

                ship_m = re.search(r"shipping\s*([$€£]?\d+(?:\.\d+)?)", sub, re.I)
                ship = ship_m.group(1) if ship_m else "N/A"
                data[code] = {"price": price, "shipping": ship}

        return data

    # expose for testing
    globals()["parse_prices"] = parse_prices

    def _parse_slash_values(line: str):
        vals = [v.strip() for v in line.split('/')]
        return [v for v in vals if v]

    def parse_profits(text: str, countries):
        """Return profit per unit mapped to given countries."""
        m = re.search(r"profit[^:]*:([^\n]+)", text, re.I)
        if not m:
            return {}
        values = re.findall(r"[$€£]?\d+(?:\.\d+)?", m.group(1))
        if not values:
            values = _parse_slash_values(m.group(1))
        return {c: v for c, v in zip(countries, values)}

    globals()["parse_profits"] = parse_profits

    def parse_margins(text: str, countries):
        """Return margin values mapped to countries."""
        m = re.search(r"margin[^:]*:([^\n]+)", text, re.I)
        if not m:
            return {}
        values = re.findall(r"\d+(?:\.\d+)?%", m.group(1))
        if not values:
            values = _parse_slash_values(m.group(1))
        return {c: v for c, v in zip(countries, values)}

    globals()["parse_margins"] = parse_margins

    def parse_delivery_times(text: str):
        """Return delivery time per country."""
        pairs = re.findall(r"To\s*([A-Za-z]{2,3})\s*:\s*([\d-]+\s*days)", text, re.I)
        return {c.upper(): t.strip() for c, t in pairs}

    globals()["parse_delivery_times"] = parse_delivery_times

    def parse_weight(text: str):
        """Extract gross weight value if present."""
        m = re.search(r"Gross Weight:\s*([^\n]+)", text, re.I)
        return m.group(1).strip() if m else ""

    globals()["parse_weight"] = parse_weight

    def parse_units_sold(text: str):
        """Extract units sold value if present."""
        m = re.search(r"Units Sold:?\s*([\d,]+)", text, re.I)
        return m.group(1).strip() if m else ""

    globals()["parse_units_sold"] = parse_units_sold

    def parse_shipping_times(text: str) -> str:
        """Return shipping time string if present."""
        m = re.search(r"Shipping Time[s]?\s*:\s*([^\n]+)", text, re.I)
        return m.group(1).strip() if m else ""

    globals()["parse_shipping_times"] = parse_shipping_times

    def remove_price_sections(text: str, codes):
        parts = []
        for piece in re.split(r"[\n,;]+", text):
            p = piece.strip()
            if not p:
                continue
            if any(p.startswith(c) for c in codes):
                continue
            parts.append(p)
        return " ".join(parts)

    # expose helper
    globals()["remove_price_sections"] = remove_price_sections

    async def format_description(text: str) -> str:
        """Return a formatted product description."""
        if not text.strip():
            return ""

        cleaned = re.sub(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b", "", text)
        cleaned = re.sub(r"Keyword.*$", "", cleaned, flags=re.I | re.S).strip()
        cleaned = cleaned.replace("Goshippro", "Hause")
        cleaned = re.sub(r"^.*keyword on.*$", "", cleaned, flags=re.I | re.M)
        price_info = parse_prices(cleaned)
        profits = parse_profits(cleaned, list(price_info.keys()))
        margins = parse_margins(cleaned, list(price_info.keys()))
        delivery = parse_delivery_times(cleaned)
        shipping_time = parse_shipping_times(cleaned)
        weight = parse_weight(cleaned)
        sold = parse_units_sold(cleaned)

        title_source = re.sub(r"To\s*[A-Za-z]{2,3}[^\n]*days(?:\s*/\s*To\s*[A-Za-z]{2,3}[^\n]*days)*", "", cleaned, flags=re.I)
        title_source = re.sub(r"Gross Weight:[^\n]+", "", title_source, flags=re.I)
        title_source = re.sub(r"Units Sold:?[^\n]+", "", title_source, flags=re.I)
        title_source = re.sub(r"Shipping Time[s]?:[^\n]+", "", title_source, flags=re.I)
        title = remove_price_sections(title_source, price_info.keys()).strip()
        category = await run_in_thread(
            call_mcp,
            f"Categorize this product title: {title}. Only return the category."
        )

        lines = [f"**{title}**", f"_Category: {category}_", ""]
        for code, vals in price_info.items():
            flag = FLAG_MAP.get(code, code)
            shipping = (
                f" + {vals['shipping']} shipping" if vals['shipping'] != "N/A" else ""
            )
            extra_parts = []
            if code in profits:
                extra_parts.append(f"Profit: {profits[code]}")
            if code in margins:
                extra_parts.append(f"Margin: {margins[code]}")
            extra = f" ({', '.join(extra_parts)})" if extra_parts else ""
            lines.append(f"{flag} {vals['price']}{shipping}{extra}")

        if delivery:
            parts = [f"To {c}: {t}" for c, t in delivery.items()]
            lines.append("Delivery: " + "/".join(parts))
        if weight:
            lines.append(f"Gross Weight: {weight}")
        if sold:
            lines.append(f"Units Sold: {sold}")
        if shipping_time:
            lines.append(f"Shipping Time: {shipping_time}")
        return "\n".join(lines)

    # expose for external use
    globals()["format_description"] = format_description

    @bot.command(
        name="formatproduct",
        description="Format a raw product description",
        usage="<raw description>"
    )
    async def formatproduct(ctx, *, args: str):
        await ctx.message.delete()
        result = await format_description(args)
        if not result:
            await ctx.send("Provide a description.")
            return
        await ctx.send(result)

product_formatter()

if __name__ == "__main__":  # pragma: no cover - manual execution
    pass
