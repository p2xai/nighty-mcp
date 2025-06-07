import builtins
import importlib
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
