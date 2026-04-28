"""ANDES backend initialization helpers."""

from __future__ import annotations

from typing import Any


def initialize_andes() -> Any:
    """Import and return the ANDES package handle.

    This is a single integration point so the rest of PyDML can stay lightweight.
    """

    try:
        import andes
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "ANDES is required but not available. Install project dependencies with: pip install -e ."
        ) from exc
    return andes
