"""Compatibility shim for `from multipart.multipart import ...` imports."""

from python_multipart.multipart import *  # noqa: F403

try:
    from python_multipart.multipart import __all__ as _all  # noqa: F401
except ImportError:  # pragma: no cover - defensive
    _all = []

__all__ = list(_all)
