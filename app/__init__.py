"""Compatibility package for the canonical implementation."""
from pathlib import Path as _Path
_package = (_Path(__file__).resolve().parent.parent / 'backend/app').resolve()
__path__ = [str(_package)]
__file__ = str(_package / '__init__.py')
exec(compile(_Path(__file__).read_bytes(), __file__, 'exec'), globals())
