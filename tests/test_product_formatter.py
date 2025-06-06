import builtins
import importlib
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
