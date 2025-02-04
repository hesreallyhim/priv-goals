import os
import sys
from regex import E
import yaml
import inquirer
from getpass import getpass
from pathlib import Path

def create_config_directory() -> Path:
    """
    Create configuration directory in user's home folder.

    Returns:
        Path: The path to the created configuration directory.
    
    Raises:
        KeyboardInterrupt: If user cancels the installation process.
    """
    config_dir = Path.home() / ".priv-goals"
    config_dir.mkdir(exist_ok=True)
    return config_dir

def get_llm_preferences():
    """Prompt user for LLM preferences."""
    questions = [
        inquirer.List('llm_provider',
                    message="Which LLM provider would you like to use?",
                    choices=['OpenAI', 'Anthropic', 'Ollama', 'Custom'],
                    default='OpenAI'),
    ]
    answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)
    
    if answers['llm_provider'] == 'Custom':
        base_url = input("Enter your LLM API base URL: ")
    else:
        base_url = {
            'OpenAI': 'https://api.openai.com/v1',
            'Anthropic': 'https://api.anthropic.com/v1',
            'Ollama': 'http://localhost:11434'
        }[answers['llm_provider']]
    
    api_key = getpass("Enter your API key (leave blank for Ollama): ").strip()
    
    # Model selection based on provider
    if answers['llm_provider'] == 'OpenAI':
        model_choices = ['gpt-4', 'gpt-3.5-turbo']
    elif answers['llm_provider'] == 'Anthropic':
        model_choices = ['claude-3-opus-20240229', 'claude-3-sonnet-20240229']
    elif answers['llm_provider'] == 'Ollama':
        model_choices = ['llama2', 'mistral', 'mixtral']
    else:
        model_choices = []
    
    if model_choices:
        questions = [
            inquirer.List('model',
                        message="Which model would you like to use?",
                        choices=model_choices,
                        default=model_choices[0])
        ]
        model = inquirer.prompt(questions, raise_keyboard_interrupt=True)['model']
    else:
        model = input("Enter your model name: ")
    
    return {
        'provider': answers['llm_provider'].lower(),
        'api_key': api_key,
        'api_base': base_url,
        'model': model
    }

def get_storage_preferences():
    """Prompt user for storage preferences."""
    questions = [
        inquirer.List('storage_type',
                     message="Where would you like to store your goals?",
                     choices=['Local CSV', 'Google Sheets'],
                     default='Local CSV'),
    ]
    
    answers = inquirer.prompt(questions, raise_keyboard_interrupt=True)
    
    config = {
        'storage_type': 'csv' if answers['storage_type'] == 'Local CSV' else 'google_sheets'
    }
    
    if answers['storage_type'] == 'Google Sheets':
        print("\nTo use Google Sheets, you'll need a service account key:")
        print("1. Go to Google Cloud Console")
        print("2. Create a project or select existing one")
        print("3. Enable Google Sheets API")
        print("4. Create a service account and download the JSON key")
        
        while True:
            key_path = input("\nEnter the path to your service account JSON key: ")
            if os.path.exists(key_path):
                config['google_sheets_credentials'] = key_path
                sheet_name = input("Enter your Google Sheet name (default: PRIV GOALS): ")
                config['google_sheets_name'] = sheet_name or "PRIV GOALS"
                break
            print("File not found. Please try again.")
    
    return config

def main():
    """Run the installation process."""
    print("Welcome to priv-goals! Let's get you set up.")
    
    try:
        config_dir = create_config_directory()
        config = {}
        
        # Get LLM preferences
        print("\nFirst, let's configure your Language Model settings.")
        config.update(get_llm_preferences())
        
        # Get storage preferences
        print("\nNext, let's set up your storage preferences.")
        config.update(get_storage_preferences())
        
        # Save configuration
        config_path = config_dir / "config.yml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"\nConfiguration saved to {config_path}")
        print("\nInstallation complete! To start priv-goals, run:")
        print("    priv-goals")
        
        return 0
    except KeyboardInterrupt:
        print("\nInstallation terminated by user")
        sys.exit(0)
