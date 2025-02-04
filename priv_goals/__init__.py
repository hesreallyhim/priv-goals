"""Privacy-focused goal tracking application with AI assistance.

This package provides a local-first goal tracking system that integrates with
various LLM providers while maintaining user privacy.
"""

from importlib import metadata
from pathlib import Path

# Package metadata
try:
    __version__ = metadata.version("priv-goals")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"

# Core functionality exports
from .app import create_app
from .storage import GoalStorage, CSVStorage, GoogleSheetsStorage
from .config import ConfigLoader, ConfigValidator

# Convenience function to get default config path
def get_default_config_path() -> Path:
    """Get the default configuration file path.
    
    Returns:
        Path to the default configuration file (~/.priv-goals/config.yml)
    """
    return Path.home() / ".priv-goals" / "config.yml"

# Define public API
__all__ = [
    "__version__",
    "create_app",
    "GoalStorage",
    "CSVStorage",
    "GoogleSheetsStorage",
    "ConfigLoader",
    "ConfigValidator",
    "get_default_config_path",
]
