"""Compatibility shim for Starlette's legacy `multipart` import.

Starlette still imports `multipart` which triggers a deprecation warning in the
python-multipart package. This module re-exports python_multipart so the import
path remains valid without the warning.
"""

from python_multipart import *  # noqa: F403
from python_multipart import __version__ as __version__

try:
    from python_multipart import __all__ as _all  # noqa: F401
except ImportError:  # pragma: no cover - defensive
    _all = []

__all__ = list(_all)
