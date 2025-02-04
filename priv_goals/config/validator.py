"""Configuration validation module.

This module provides functionality to validate configuration settings through the
ConfigValidator class, ensuring all required fields are present and have valid values.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse

from priv_goals.exceptions import ConfigValidationError

class ConfigValidator:
    """Class responsible for validating configuration settings."""

    VALID_PROVIDERS = {'openai', 'anthropic', 'ollama', 'custom'}
    VALID_STORAGE_TYPES = {'csv', 'google_sheets'}
    PROVIDER_MODELS = {
        'openai': ['gpt-4', 'gpt-3.5-turbo'],
        'anthropic': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229'],
        'ollama': ['llama2', 'mistral', 'mixtral'],
    }
    REQUIRED_FIELDS = ['provider', 'model', 'storage_type']
    GOOGLE_SHEETS_REQUIRED_FIELDS = ['google_sheets_credentials', 'google_sheets_name']

    @classmethod
    def validate_config(cls, config_path: Path) -> bool:
        """Validate the configuration file at the given path.

        Args:
            config_path: Path to the configuration file

        Returns:
            bool: True if configuration is valid

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if not config_path.exists():
            raise ConfigValidationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
        except Exception as e:
            raise ConfigValidationError(f"Failed to load configuration: {str(e)}")

        return cls.validate_config_dict(config)

    @classmethod
    def validate_config_dict(cls, config: Dict[str, Any]) -> bool:
        """Validate the configuration dictionary.

        Args:
            config: Configuration dictionary to validate

        Returns:
            bool: True if configuration is valid

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        # Required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in config:
                raise ConfigValidationError(f"Missing required field: {field}")

        # Validate provider settings
        cls._validate_provider_settings(config)

        # Validate storage settings
        cls._validate_storage_settings(config)

        return True

    @classmethod
    def _validate_provider_settings(cls, config: Dict[str, Any]) -> None:
        """Validate LLM provider settings.

        Args:
            config: Configuration dictionary

        Raises:
            ConfigValidationError: If provider settings are invalid
        """
        provider = config['provider'].lower()
        
        if provider not in cls.VALID_PROVIDERS:
            raise ConfigValidationError(
                f"Invalid provider: {provider}. Must be one of: {', '.join(cls.VALID_PROVIDERS)}"
            )

        # Validate API key (not required for Ollama)
        if provider != 'ollama':
            api_key = config.get('api_key')
            if not api_key:
                raise ConfigValidationError(f"API key required for {provider}")
            if not isinstance(api_key, str):
                raise ConfigValidationError("API key must be a string")
            if not api_key.startswith('$KEYRING_') and len(api_key.strip()) < 8:
                raise ConfigValidationError("API key appears to be invalid")

        # Validate API base URL
        api_base = config.get('api_base')
        if not api_base:
            raise ConfigValidationError("Missing api_base URL")
        try:
            parsed_url = urlparse(api_base)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ConfigValidationError(f"Invalid api_base URL: {api_base}")
        except Exception as e:
            raise ConfigValidationError(f"Invalid api_base URL: {str(e)}")

        # Validate model based on provider
        model = config['model']
        if not isinstance(model, str):
            raise ConfigValidationError("Model must be a string")

        cls._validate_model_for_provider(provider, model)

    @classmethod
    def _validate_model_for_provider(cls, provider: str, model: str) -> None:
        """Validate that the model is appropriate for the provider.

        Args:
            provider: LLM provider name
            model: Model name to validate

        Raises:
            ConfigValidationError: If model is invalid for the provider
        """
        if provider in cls.PROVIDER_MODELS and model not in cls.PROVIDER_MODELS[provider]:
            raise ConfigValidationError(
                f"Invalid model '{model}' for provider '{provider}'. "
                f"Valid models are: {', '.join(cls.PROVIDER_MODELS[provider])}"
            )

    @classmethod
    def _validate_storage_settings(cls, config: Dict[str, Any]) -> None:
        """Validate storage backend settings.

        Args:
            config: Configuration dictionary

        Raises:
            ConfigValidationError: If storage settings are invalid
        """
        storage_type = config['storage_type']
        
        if storage_type not in cls.VALID_STORAGE_TYPES:
            raise ConfigValidationError(
                f"Invalid storage_type: {storage_type}. "
                f"Must be one of: {', '.join(cls.VALID_STORAGE_TYPES)}"
            )

        if storage_type == 'google_sheets':
            cls._validate_google_sheets_settings(config)

    @classmethod
    def _validate_google_sheets_settings(cls, config: Dict[str, Any]) -> None:
        """Validate Google Sheets specific settings.

        Args:
            config: Configuration dictionary

        Raises:
            ConfigValidationError: If Google Sheets settings are invalid
        """
        for field in cls.GOOGLE_SHEETS_REQUIRED_FIELDS:
            if field not in config:
                raise ConfigValidationError(f"Missing required field for Google Sheets: {field}")

        credentials_path = config['google_sheets_credentials']
        
        # Handle keyring reference
        if credentials_path == '$KEYRING_GOOGLE_CREDENTIALS':
            return

        # Validate credentials file exists and is readable
        if not os.path.exists(credentials_path):
            raise ConfigValidationError(
                f"Google Sheets credentials file not found: {credentials_path}"
            )
        
        try:
            with open(credentials_path) as f:
                credentials = yaml.safe_load(f)
                if not isinstance(credentials, dict):
                    raise ConfigValidationError("Invalid credentials format")
        except Exception as e:
            raise ConfigValidationError(
                f"Failed to load Google Sheets credentials: {str(e)}"
            )

        # Validate sheet name
        sheet_name = config['google_sheets_name']
        if not isinstance(sheet_name, str) or not sheet_name.strip():
            raise ConfigValidationError("Invalid Google Sheets name")
