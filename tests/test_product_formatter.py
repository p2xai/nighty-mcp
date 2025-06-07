import builtins
import importlib
import asyncio
import re
import sys
import types
from pathlib import Path

# Stub required globals and modules before importing the script
builtins.nightyScript = lambda *a, **k: (lambda f: f)
builtins.bot = types.SimpleNamespace(command=lambda *a, **k: (lambda f: f))
sys.modules['discord'] = types.ModuleType('discord')
sys.modules['requests'] = types.ModuleType('requests')

# Ensure repository root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import product_formatter

parse_prices = product_formatter.parse_prices
parse_profits = product_formatter.parse_profits
parse_margins = product_formatter.parse_margins
parse_delivery_times = product_formatter.parse_delivery_times
parse_weight = product_formatter.parse_weight
parse_units_sold = product_formatter.parse_units_sold
format_description = product_formatter.format_description


def _clean_text(text: str) -> str:
    text = re.sub(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b", "", text)
    text = re.sub(r"Keyword.*$", "", text, flags=re.I | re.S).strip()
    text = text.replace("Goshippro", "Hause")
    return re.sub(r"^.*keyword on.*$", "", text, flags=re.I | re.M)


def test_parse_prices_country_leading():
    text = "USA $99 shipping $10, UK £80 shipping £5"
    result = parse_prices(text)
    assert result == {
        "USA": {"price": "$99", "shipping": "$10"},
        "UK": {"price": "£80", "shipping": "£5"},
    }


def test_parse_prices_price_to_country():
    text = "$99 to USA / £80 to UK"
    result = parse_prices(text)
    assert result == {
        "USA": {"price": "$99", "shipping": "N/A"},
        "UK": {"price": "£80", "shipping": "N/A"},
    }


def test_parse_prices_mixed_formats():
    text = "USA $70 shipping $5 / €60 to DE"
    result = parse_prices(text)
    assert result == {
        "USA": {"price": "$70", "shipping": "$5"},
        "DE": {"price": "€60", "shipping": "N/A"},
    }


def test_clean_replaces_goshippro():
    text = "Buy from Goshippro 2024-07-01"
    assert _clean_text(text) == "Buy from Hause"


def test_clean_removes_keyword_on_line():
    text = "Line1\nkeyword on sale\nLine2"
    cleaned = _clean_text(text)
    assert re.search(r"keyword on", cleaned, re.I) is None


def test_parse_prices_ignores_non_country_line():
    text = "Gross Weight: 0.2kg"
    result = parse_prices(text)
    assert result == {}


def test_parse_profits_and_margins():
    text = (
        "USA $99 shipping $10, UK £80 shipping £5\n"
        "Profit Per Unit (Hause): $11/$12\n"
        "Margin: 5%/6%"
    )
    prices = parse_prices(text)
    order = list(prices.keys())
    profits = parse_profits(text, order)
    margins = parse_margins(text, order)
    assert profits == {"USA": "$11", "UK": "$12"}
    assert margins == {"USA": "5%", "UK": "6%"}


def test_format_description_includes_profit_margin():
    product_formatter.call_mcp = lambda *a, **k: "Test"
    text = (
        "USA $99 shipping $10, UK £80 shipping £5\n"
        "Profit Per Unit (Hause): $11/$12\n"
        "Margin: 5%/6%\n"
        "Amazing Item"
    )
    result = asyncio.run(format_description(text))
    lines = result.splitlines()
    assert lines[3] == "\U0001F1FA\U0001F1F8 $99 + $10 shipping (Profit: $11, Margin: 5%)"
    assert lines[4] == "\U0001F1EC\U0001F1E7 £80 + £5 shipping (Profit: $12, Margin: 6%)"


def test_parse_delivery_weight_units():
    text = (
        "USA $10\n"
        "To USA: 6-15 days/To EU: 6-9 days\n"
        "Gross Weight: 0.2kg\n"
        "Units Sold: 500"
    )
    assert parse_delivery_times(text) == {"USA": "6-15 days", "EU": "6-9 days"}
    assert parse_weight(text) == "0.2kg"
    assert parse_units_sold(text) == "500"


def test_format_description_includes_extra_details():
    product_formatter.call_mcp = lambda *a, **k: "Test"
    text = (
        "USA $99 shipping $10, UK £80 shipping £5\n"
        "To USA: 6-15 days/To EU: 6-9 days\n"
        "Gross Weight: 0.2kg\n"
        "Units Sold: 300\n"
        "Amazing Item"
    )
    result = asyncio.run(format_description(text))
    lines = result.splitlines()
    assert lines[3] == "\U0001F1FA\U0001F1F8 $99 + $10 shipping"
    assert lines[4] == "\U0001F1EC\U0001F1E7 £80 + £5 shipping"
    assert lines[5] == "Delivery: To USA: 6-15 days/To EU: 6-9 days"
    assert lines[6] == "Gross Weight: 0.2kg"
    assert lines[7] == "Units Sold: 300"
