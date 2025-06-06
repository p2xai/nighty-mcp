import builtins
import importlib
import re
import sys
import types
from pathlib import Path

# Stub globals and modules before importing product_formatter
builtins.nightyScript = lambda *a, **k: (lambda f: f)

_captured = {}

def _capture_command(*a, **k):
    def decorator(f):
        _captured['formatproduct'] = f
        return f
    return decorator

builtins.bot = types.SimpleNamespace(command=_capture_command)
sys.modules['discord'] = types.ModuleType('discord')
sys.modules['requests'] = types.ModuleType('requests')

# Ensure repository root on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import product_formatter
importlib.reload(product_formatter)  # ensure decorator capture

parse_prices = product_formatter.parse_prices
remove_price_sections = product_formatter.remove_price_sections


def _clean_text(text: str) -> str:
    text = re.sub(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b", "", text)
    return re.sub(r"Keyword.*$", "", text, flags=re.I | re.S).strip()


def test_country_leading_format():
    text = "USA $99 shipping $10, UK £80 shipping £5, Amazing Item 2024-06-30 Keyword: sale"
    cleaned = _clean_text(text)
    prices = parse_prices(cleaned)
    title = remove_price_sections(cleaned, prices.keys()).strip()
    assert prices == {
        "USA": {"price": "$99", "shipping": "$10"},
        "UK": {"price": "£80", "shipping": "£5"},
    }
    assert title == "Amazing Item"


def test_price_to_country_format():
    text = "$99 to USA / £80 to UK; Another Item"
    cleaned = _clean_text(text)
    prices = parse_prices(cleaned)
    title = remove_price_sections(cleaned, prices.keys()).strip()
    assert prices == {
        "USA": {"price": "$99", "shipping": "N/A"},
        "UK": {"price": "£80", "shipping": "N/A"},
    }
    # remove_price_sections does not drop price-to-country pieces
    assert title == "$99 to USA / £80 to UK Another Item"
