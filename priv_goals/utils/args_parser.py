"""Command line argument parsing for the priv-goals application.

This module handles all command-line argument parsing, providing a centralized
way to manage and validate application arguments.
"""

import argparse
from pathlib import Path
from typing import Optional
import sys

from priv_goals.constants import DEFAULT_LOG_DIR

from .logger import Logger

class ArgsParser:
    """Handles command line argument parsing for the application."""
    
    # Constants for default values
    DEFAULT_PORT = 7860
    DEFAULT_CONFIG_PATH = Path.home() / ".priv-goals" / "config.yml"

    def __init__(self):
        """Initialize the argument parser."""
        self.parser = self._create_parser()
        self.args: Optional[argparse.Namespace] = None
        self.logger = None

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser.
        
        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Privacy-focused goal tracking application with AI assistance.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  priv-goals                 # Start the application
  priv-goals --setup         # Run the setup wizard
  priv-goals --port 8080     # Start on specific port
  priv-goals --config ~/my-config.yml  # Use custom config file
            """
        )
        
        parser.add_argument(
            "--setup",
            action="store_true",
            help="Run the interactive setup wizard"
        )
        
        parser.add_argument(
            "--port",
            type=self._validate_port,
            default=self.DEFAULT_PORT,
            help=f"Port to run the web interface on (default: {self.DEFAULT_PORT})"
        )
        
        parser.add_argument(
            "--config",
            type=Path,
            default=self.DEFAULT_CONFIG_PATH,
            help=f"Path to configuration file (default: {self.DEFAULT_CONFIG_PATH})"
        )
        
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode with additional logging"
        )
        
        parser.add_argument(
            "--log-dir",
            type=Path,
            default=DEFAULT_LOG_DIR,
            help=f"Directory for log files (default: {DEFAULT_LOG_DIR})"
        )
        
        parser.add_argument(
            "--version",
            action="version",
            version="%(prog)s 0.0.1",
            help="Show program's version number and exit"
        )
        
        return parser

    def parse_args(self) -> argparse.Namespace:
        """Parse and validate command line arguments.
        
        Returns:
            Namespace containing the parsed arguments
            
        Example:
            >>> parser = ArgsParser()
            >>> args = parser.parse_args()
            >>> print(args.debug)
            False
            >>> print(args.port)
            7860
        """
        self.args = self.parser.parse_args()
        
        # Create log directory if it doesn't exist
        self.args.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging for argument parsing
        self.logger = Logger(
            log_dir=self.args.log_dir,
            debug=self.args.debug,
            component="args_parser"
        ).get_logger()
        
        self.logger.debug("Debug mode enabled")
        self.logger.debug("Parsed arguments: %s", vars(self.args))
        
        # Only validate config path if not in setup mode
        if not self.args.setup and not self.args.config.exists():
            self.logger.debug(f"Configuration file does not exist: {self.args.config}")
            print("Configuration file does not exist. Please run the setup wizard (priv-goals --setup)")
            sys.exit(0)
        
        self.logger.info("Arguments parsed successfully")
        
        return self.args

    @staticmethod
    def _validate_port(value: str) -> int:
        """Validate the port number argument.
        
        Args:
            value: Port number as string
            
        Returns:
            Validated port number as integer
            
        Raises:
            argparse.ArgumentTypeError: If port number is invalid
        """
        try:
            port = int(value)
            if not (1024 <= port <= 65535):
                raise argparse.ArgumentTypeError(
                    f"Port must be between 1024 and 65535, got {port}"
                )
            return port
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Port must be a number, got {value!r}"
            )
