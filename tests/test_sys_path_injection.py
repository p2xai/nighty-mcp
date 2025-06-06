import builtins
import importlib.util
import sys
import types
from pathlib import Path

# stub dependencies
builtins.nightyScript = lambda *a, **k: (lambda f: f)
builtins.bot = types.SimpleNamespace(
    command=lambda *a, **k: (lambda f: f), event=lambda f: f
)
sys.modules['discord'] = types.ModuleType('discord')
sys.modules['requests'] = types.ModuleType('requests')
sys.modules['emoji'] = types.ModuleType('emoji')
sys.modules['emoji'].emojize = lambda val, language=None: val

repo = Path(__file__).resolve().parents[1]
if str(repo) in sys.path:
    sys.path.remove(str(repo))

spec = importlib.util.spec_from_file_location('channel_importer', repo / 'channel_importer.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert str(repo) in sys.path
