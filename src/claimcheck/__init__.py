"""Market claim verification against SEC EDGAR facts."""

from .config import Settings, load_settings
from .edgar import EdgarClient

__all__ = ["EdgarClient", "Settings", "load_settings"]
