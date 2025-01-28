#!/bin/bash

# Function to check Python version
check_python_version() {
    REQUIRED_VERSION="3.8"
    CURRENT_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$CURRENT_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
        echo "Python $REQUIRED_VERSION or higher is required. Found Python $CURRENT_VERSION."
        exit 1
    fi
}

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 is not installed. Please install it and try again."
        exit 1
    fi
}

# Check for Python and required tools
check_command python3
check_command tree
check_python_version

# Set the local Python version using pyenv
PYTHON_LOCAL_VERSION="3.12.8"
echo "$PYTHON_LOCAL_VERSION" > .python-version
echo ".python-version file created with Python version: $PYTHON_LOCAL_VERSION"

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating the virtual environment..."
source venv/bin/activate

# Create the directory structure
mkdir -p config

# Create .env file (leave it blank for now)
touch .env

# Create .env.example file with example content
cat <<EOL > .env.example
# Path to your Google Service Account JSON file
GOOGLE_SERVICE_ACCOUNT=config/service_account.json
EOL

# Create .gitignore file with content
cat <<EOL > .gitignore
# Ignore the virtual environment
venv/
# Ignore the credentials file and environment file
config/service_account.json
.env
EOL

# Create requirements.txt file with content
cat <<EOL > requirements.txt
gradio
gspread
oauth2client
pandas
python-dotenv
EOL

# Upgrade pip inside the virtual environment
echo "Upgrading pip inside the virtual environment..."
pip install --upgrade pip

# Install dependencies in the virtual environment
echo "Installing dependencies..."
pip install -r requirements.txt

# Create app.py as a placeholder (optional)
cat <<EOL > app.py
# Placeholder for the Squad Goals main application
# To be implemented with Gradio and Google Sheets integration
if __name__ == "__main__":
    print("Welcome to Squad Goals!")
EOL

# Confirm the directory structure
echo "Directory structure, virtual environment, and files have been created:"
tree .

# Provide final instructions to the user
echo -e "\nSetup is complete!"
echo -e "To activate the virtual environment in the future, use:"
echo "source venv/bin/activate"
echo -e "To deactivate the virtual environment, use:"
echo "deactivate"
