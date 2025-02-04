"""Main entry point for the priv-goals application."""

import sys
import gradio as gr
from typing import NoReturn, Tuple
import argparse

from .app import create_app
from .config.loader import ConfigLoader
from .exceptions import ConfigurationError
from .utils.args_parser import ArgsParser
from .utils.logger import Logger

def setup_application() -> Tuple[Logger, gr.Blocks, argparse.Namespace]:
    """Initialize application components.
    
    Returns:
        Tuple of (logger, gradio application, parsed arguments)
        
    Raises:
        ConfigurationError: If configuration is invalid or missing
        Exception: For other initialization errors
    """
    # Parse command line arguments
    parser = ArgsParser()
    args = parser.parse_args()
    
    # Initialize logging
    logger = Logger(
        log_dir=args.log_dir,
        debug=args.debug,
        component="main"
    ).get_logger()
    
    # Set default log level to INFO for all components
    Logger.update_log_levels({
        "priv_goals": "INFO",
        "priv_goals.config": "INFO",
        "priv_goals.storage": "INFO",
        "priv_goals.utiils": "INFO"
    })
    
    # Handle setup wizard if requested
    if args.setup:
        logger.info("Running setup wizard")
        from scripts.install import main as setup_main
        sys.exit(setup_main())
    
    # Load configuration
    logger.info("Loading configuration from %s", args.config)
    with ConfigLoader(args.config) as loader:
        config = loader.load_config()
    
    # Create application
    logger.info("Creating application")
    app = create_app(config=config, debug=args.debug)
    
    return logger, app, args

def main() -> NoReturn:
    """Main entry point for the application.
    
    This function:
    1. Sets up logging
    2. Handles the setup wizard if requested
    3. Validates and loads configuration
    4. Creates and launches the web interface
    
    Exit codes:
        0: Success
        1: Configuration error
        2: Application error
    """
    try:
        # Setup application and get components
        logger, app, args = setup_application()
        
        # Launch the web interface
        logger.info("Launching web interface on port %d", args.port)
        app.launch(
            app,
            debug=True if args.debug else False,
            server_name="127.0.0.1",
            server_port=args.port,
            share=False
        )
        
        sys.exit(0)
        
    except ConfigurationError as e:
        print(f"Configuration Error: {str(e)}")
        print("Please run 'priv-goals --setup' to configure the application")
        sys.exit(1)
        
    except KeyboardInterrupt as e:
        print("\nApplication terminated by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if getattr(args, 'debug', False):
            raise
        print("Run with --debug for more information")
        sys.exit(2)

if __name__ == "__main__":
    main()
