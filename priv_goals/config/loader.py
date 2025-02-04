"""Configuration loader with secure credential handling.

This module handles loading and resolving configuration settings, including
secure credential management using the system keyring.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any

from priv_goals.exceptions import ConfigurationError
from priv_goals.utils import KeyStorage, Logger

class ConfigLoader:
    """Handles loading and resolving configuration settings."""
    
    def __init__(self, config_path: Path):
        """Initialize the config loader.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.temp_files: list[Path] = []
        
        # Initialize logger for this component
        self.logger = Logger(
            log_dir=Path.home() / ".priv-goals" / "logs",
            component="config.loader"
        ).get_logger()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup of temporary files."""
        self._cleanup_temp_files()
    
    def load_config(self) -> Dict[str, Any]:
        """Load and resolve configuration settings.
        
        Returns:
            Dict containing the complete configuration with resolved credentials
            
        Raises:
            ConfigurationError: If configuration cannot be loaded or credentials 
                              cannot be resolved
        """
        try:
            self.logger.debug("Loading configuration from %s", self.config_path)
            config = self._load_yaml_config()
            return self._resolve_credentials(config)
        except Exception as e:
            self.logger.error("Failed to load configuration", exc_info=True)
            raise ConfigurationError(f"Failed to load configuration: {str(e)}") from e
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load the raw YAML configuration file.
        
        Returns:
            Dict containing the raw configuration
            
        Raises:
            ConfigurationError: If the file cannot be read or parsed
        """
        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            self.logger.error("Error reading config file", exc_info=True)
            raise ConfigurationError(f"Error reading config file: {str(e)}") from e
    
    def _resolve_credentials(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve and inject secure credentials into configuration.
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            Configuration with resolved credentials
            
        Raises:
            ConfigurationError: If credentials cannot be resolved
        """
        config = config.copy()  # Don't modify the input dict
        
        # Resolve API key if stored in keyring
        if config.get('api_key', '').startswith('$KEYRING_'):
            provider = config.get('provider')
            if not provider:
                self.logger.error("Provider not specified in configuration")
                raise ConfigurationError("Provider not specified in configuration")
            
            api_key = self._get_api_key(provider)
            if not api_key:
                self.logger.error("API key not found for provider %s", provider)
                raise ConfigurationError(f"API key for {provider} not found in keyring")
            config['api_key'] = api_key
        
        # Resolve Google credentials if stored in keyring
        if config.get('storage_type') == 'google_sheets':
            if config.get('google_sheets_credentials') == '$KEYRING_GOOGLE_CREDENTIALS':
                config = self._resolve_google_credentials(config)
        
        return config
    
    def _get_api_key(self, provider: str) -> str | None:
        """Get API key from keyring for the specified provider.
        
        Args:
            provider: Name of the LLM provider
            
        Returns:
            API key if found, None otherwise
        """
        try:
            self.logger.debug("Retrieving API key for provider %s", provider)
            return KeyStorage.get_api_key(provider)
        except Exception as e:
            self.logger.error(
                "Failed to retrieve API key for provider %s", 
                provider, 
                exc_info=True
            )
            return None
    
    def _resolve_google_credentials(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve Google credentials and create temporary credential file.
        
        Args:
            config: Current configuration dictionary
            
        Returns:
            Updated configuration with resolved credentials
            
        Raises:
            ConfigurationError: If credentials cannot be resolved
        """
        credentials = KeyStorage.get_google_credentials()
        if not credentials:
            self.logger.error("Google Sheets credentials not found in keyring")
            raise ConfigurationError("Google Sheets credentials not found in keyring")
        
        # Create temporary credentials file
        temp_creds_path = Path.home() / '.priv-goals' / '.temp_credentials.json'
        try:
            temp_creds_path.parent.mkdir(exist_ok=True)
            with open(temp_creds_path, 'w') as f:
                json.dump(credentials, f)
            
            # Track for cleanup
            self.temp_files.append(temp_creds_path)
            self.logger.debug(
                "Created temporary credentials file at %s", 
                temp_creds_path
            )
            
            config['google_sheets_credentials'] = str(temp_creds_path)
            return config
            
        except Exception as e:
            if temp_creds_path.exists():
                temp_creds_path.unlink()
            self.logger.error(
                "Failed to create temporary credentials file", 
                exc_info=True
            )
            raise ConfigurationError(
                f"Failed to create temporary credentials file: {str(e)}"
            ) from e
    
    def _cleanup_temp_files(self) -> None:
        """Clean up any temporary files created during configuration loading."""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    self.logger.debug("Removed temporary file %s", temp_file)
            except Exception as e:
                self.logger.warning(
                    "Failed to remove temporary file %s: %s",
                    temp_file,
                    str(e)
                )
