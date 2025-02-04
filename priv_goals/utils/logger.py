"""Logging configuration for the priv-goals application.

This module provides a centralized way to configure logging across the application,
supporting both file and console output with different log levels and formats.

Example:
    >>> logger = Logger(log_dir="~/.priv-goals/logs", debug=True).get_logger()
    >>> logger.info("Application started")
    >>> logger.debug("Processing request")
    
    # Update log levels for specific components
    >>> Logger.update_log_levels({
    ...     "priv_goals.config": "DEBUG",
    ...     "priv_goals.storage": "WARNING"
    ... })
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Union, Dict

from priv_goals.constants import DEFAULT_LOG_DIR

class Logger:
    """Handles logging configuration and management for the application.
    
    This class provides a centralized way to configure and manage logging
    across different components of the application. It supports both file
    and console output, with configurable log levels and formats.
    
    Attributes:
        DEFAULT_FORMAT: Standard log message format
        DEBUG_FORMAT: Detailed log message format for debugging
        MAX_BYTES: Maximum size for each log file (10MB)
        BACKUP_COUNT: Number of backup files to keep
        
    Example:
        >>> logger = Logger(
        ...     log_dir="~/.priv-goals/logs",
        ...     debug=True,
        ...     component="config"
        ... ).get_logger()
        >>> logger.info("Configuration loaded")
    """
    
    # Default format for log messages
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Format for debugging (includes function name and line number)
    DEBUG_FORMAT = ('%(asctime)s - %(name)s - %(levelname)s - '
                   '%(funcName)s:%(lineno)d - %(message)s')
    
    # Maximum size for each log file (10MB)
    MAX_BYTES = 10 * 1024 * 1024
    
    # Number of backup files to keep
    BACKUP_COUNT = 5

    def __init__(
        self,
        log_dir: Optional[Union[str, Path]] = None,
        debug: bool = False,
        log_to_console: bool = True,
        component: Optional[str] = None
    ):
        """Initialize logger configuration.
        
        Args:
            log_dir: Directory where log files will be stored
            debug: Whether to enable debug logging
            log_to_console: Whether to output logs to console
            component: Optional component name for specific logger setup
            
        Example:
            >>> logger = Logger("~/.priv-goals/logs", debug=True)
        """
        # Convert log_dir to Path if it's a string
        self.log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Store configuration
        self.debug = debug
        self.log_to_console = log_to_console
        
        # Determine logger name and log file path
        self.logger_name = "priv_goals"
        if component:
            self.logger_name = f"{self.logger_name}.{component}"
            self.log_file = self.log_dir / f"{component}.log"
        else:
            self.log_file = self.log_dir / "priv_goals.log"
        
        # Initialize logger
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Set up the logger with configured handlers."""
        # Create logger
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        
        # Avoid adding handlers multiple times
        if self.logger.handlers:
            return
        
        # Create formatters
        formatter = logging.Formatter(
            self.DEBUG_FORMAT if self.debug else self.DEFAULT_FORMAT
        )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self.MAX_BYTES,
            backupCount=self.BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG if self.debug else logging.INFO)
        self.logger.addHandler(file_handler)
        
        # Console handler
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            # Console shows warnings and above by default, all levels in debug mode
            console_handler.setLevel(logging.DEBUG if self.debug else logging.WARNING)
            self.logger.addHandler(console_handler)
        
        # Log startup information
        self.logger.info("Logging initialized: %s", "debug" if self.debug else "normal")
        if self.debug:
            self.logger.debug("Debug logging enabled")

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance.
        
        Returns:
            Logger instance configured according to the parameters
            
        Example:
            >>> logger = Logger("~/.priv-goals/logs").get_logger()
            >>> logger.info("Application started")
        """
        return self.logger

    @staticmethod
    def update_log_levels(levels: Dict[str, str]) -> None:
        """Update log levels for specific loggers.
        
        Args:
            levels: Dictionary mapping logger names to log levels
            
        Example:
            >>> Logger.update_log_levels({
            ...     "priv_goals.config": "DEBUG",
            ...     "priv_goals.storage": "WARNING"
            ... })
        """
        for logger_name, level in levels.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, level.upper()))
            logger.debug("Log level updated to %s", level)
