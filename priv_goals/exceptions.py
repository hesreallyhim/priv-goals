class LLMInitializationError(Exception):
    """Exception raised when initialization of the Large Language Model fails.

    This exception indicates failures during LLM setup, including:
    - Missing or invalid API keys
    - Failed environment validation
    - Connection test failures
    - Missing required model capabilities
    """
    pass

class ConfigurationError(Exception):
    """Raised when there are issues loading or resolving configuration."""
    pass


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass
