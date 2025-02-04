import keyring
import json
from pathlib import Path
from typing import Optional, Dict, Any

class KeyStorage:
    """Secure storage for sensitive credentials using system keyring."""
    
    SERVICE_NAME = "priv-goals"
    
    @staticmethod
    def store_api_key(provider: str, api_key: str) -> None:
        """Store API key in system keyring."""
        keyring.set_password(KeyStorage.SERVICE_NAME, f"{provider}_api_key", api_key)
    
    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        """Retrieve API key from system keyring."""
        return keyring.get_password(KeyStorage.SERVICE_NAME, f"{provider}_api_key")
    
    @staticmethod
    def store_google_credentials(credentials_path: str) -> None:
        """Store Google service account credentials in system keyring."""
        # Read and store the content of the credentials file
        with open(credentials_path) as f:
            credentials = json.load(f)
        keyring.set_password(
            KeyStorage.SERVICE_NAME,
            "google_credentials",
            json.dumps(credentials)
        )
        
    @staticmethod
    def get_google_credentials() -> Optional[Dict[str, Any]]:
        """Retrieve Google credentials from system keyring."""
        credentials_str = keyring.get_password(
            KeyStorage.SERVICE_NAME,
            "google_credentials"
        )
        return json.loads(credentials_str) if credentials_str else None
    
    @staticmethod
    def remove_all_keys() -> None:
        """Remove all stored keys (useful for cleanup/reset)."""
        providers = ['openai', 'anthropic', 'custom']
        for provider in providers:
            try:
                keyring.delete_password(
                    KeyStorage.SERVICE_NAME,
                    f"{provider}_api_key"
                )
            except keyring.errors.PasswordDeleteError:
                pass
        
        try:
            keyring.delete_password(
                KeyStorage.SERVICE_NAME,
                "google_credentials"
            )
        except keyring.errors.PasswordDeleteError:
            pass

def update_config_for_keyring(config_path: Path) -> None:
    """Update config.yml to use keyring references instead of raw credentials."""
    import yaml
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Store API key in keyring if present
    if config.get('api_key'):
        KeyStorage.store_api_key(config['provider'], config['api_key'])
        config['api_key'] = f"$KEYRING_{config['provider'].upper()}_API_KEY"
    
    # Store Google credentials in keyring if present
    if config.get('google_sheets_credentials'):
        creds_path = config['google_sheets_credentials']
        if Path(creds_path).exists():
            KeyStorage.store_google_credentials(creds_path)
            config['google_sheets_credentials'] = "$KEYRING_GOOGLE_CREDENTIALS"
    
    # Write updated config without raw credentials
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
