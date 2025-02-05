
## priv-goals

A privacy-focused goal-tracking application that runs locally on your machine. Track your goals, habits, and tasks with the help of AI, without sharing your data with third-party servers (NOTE: depends on your chosen configuration).

**[UNDER DEVELOPMENT]** This project is currently under development and not yet ready for active use. Bare functionality is implemented and available for exploration. Please check back later for updates.

## Features

- 🔒 **Privacy First**: All data stored locally by default
- 🤖 **AI-Powered**: Uses your preferred LLM for natural interaction
- 📊 **Flexible Storage**: Choose between local CSV or Google Sheets
- 🎯 **Goal Tracking**: Track status, progress, and completion
- ⏰ **Duration Tracking**: Monitor expected vs actual completion time
- 📝 **Notes & Updates**: Add context and track progress
- 🔑 **Secure Credentials**: All sensitive keys stored in system keyring

## Installation

### Quick Install

```bash
pip install priv-goals
priv-goals --setup
```

### Requirements

- Python 3.8 or higher
- An API key for your preferred LLM provider (OpenAI, Anthropic, etc.)
- For Google Sheets storage: Google Cloud service account credentials
- System keyring (usually pre-installed on most operating systems)

### Detailed Installation Steps

1. **Create a virtual environment (recommended)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install from PyPI**:
   ```bash
   pip install priv-goals
   ```

3. **Run the setup wizard**:
   ```bash
   priv-goals --setup
   ```
   
   The setup wizard will guide you through:
   - Choosing your LLM provider (OpenAI, Anthropic, Ollama, or custom)
   - Securely storing your API key in the system keyring
   - Selecting and configuring your model preferences
   - Choosing your storage backend (local CSV or Google Sheets)
   - Setting up any additional required credentials

4. **Start the application**:
   ```bash
   priv-goals
   ```

## Configuration

Configuration is stored in `~/.priv-goals/config.yml`. Sensitive credentials like API keys and service account details are stored securely in your system's keyring.

Example configuration:
```yaml
provider: openai
api_key: $KEYRING_OPENAI_API_KEY
api_base: https://api.openai.com/v1
model: gpt-4
storage_type: csv
```

## Storage Options

### Local CSV (Default)
- Data stored in `~/.priv-goals/goals.csv`
- Complete privacy, no external services required
- Suitable for personal use

### Google Sheets
- Requires Google Cloud service account credentials
- Great for team collaboration
- Accessible from multiple devices
- To set up:
  1. Create a Google Cloud project
  2. Enable Google Sheets API
  3. Create a service account and download credentials
  4. Run `priv-goals --setup` and select Google Sheets storage
  5. Your credentials will be securely stored in the system keyring

## Usage

1. **Start the application**:
   ```bash
   priv-goals
   ```

2. **Access the web interface**:
   Open your browser and navigate to `http://localhost:7860`

3. **Interact naturally**:
   - "Add a new goal to read a book by next month"
   - "Show me my current goals"
   - "Mark the reading goal as complete"
   - "Add a note to my exercise goal"

## Command Line Reference

### Help Message
```
usage: priv-goals [-h] [--setup] [--port PORT] [--config CONFIG] [--debug]
                  [--log-dir LOG_DIR] [--version]

Privacy-focused goal tracking application with AI assistance.

options:
  -h, --help           show this help message and exit
  --setup              Run the interactive setup wizard
  --port PORT          Port to run the web interface on (default: 7860)
  --config CONFIG      Path to configuration file (default: ~/.priv-goals/config.yml)
  --debug              Enable debug mode with additional logging
  --log-dir LOG_DIR    Directory for log files (default: ~/.priv-goals/logs)
  --version           Show program's version number and exit

Examples:
  priv-goals                 # Start the application
  priv-goals --setup         # Run the setup wizard
  priv-goals --port 8080     # Start on specific port
  priv-goals --config ~/my-config.yml  # Use custom config file
```

### Common Commands

1. **View help**:
   ```bash
   priv-goals --help
   ```

2. **Run setup wizard**:
   ```bash
   priv-goals --setup
   ```

3. **Start on custom port**:
   ```bash
   priv-goals --port 8080
   ```

4. **Enable debug logging**:
   ```bash
   priv-goals --debug
   ```

5. **Use custom config file**:
   ```bash
   priv-goals --config ~/custom-config.yml
   ```

6. **Check version**:
   ```bash
   priv-goals --version
   ```

## Security Notes

- All sensitive credentials (API keys, service account details) are stored in your system's secure keyring
- No credentials are stored in plain text
- Temporary credential files are automatically cleaned up
- Local CSV files are stored in your home directory
- Google Sheets credentials are only used when needed and stored securely

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Roadmap

### **1️⃣ Goal Management Enhancements**
- [x] **Delete/remove goals** from the tracker.
- [ ] **Rename goals** for better organization.
- [ ] **Revert a completed goal back to "in progress."**
- [ ] **Allow users to enter a duplicate goal** (e.g., "read a book") if a similar goal was previously completed.
- [ ] **Allow the user to "un-delete" a goal** that was removed by mistake. (Partially working thanks to assistant's memory.)
- [ ] **Allow multiple lists** (e.g., short-term, long-term, personal, work, etc.) for better organization.
- [ ] **Implement a "priority" column** for goals, so users can prioritize their tasks.

### **2️⃣ Time Tracking & Scheduling**
- [x] **Track timestamps**: When a goal is created, when it is completed, and how long it took.
- [ ] **Calculate and display average completion time** for goals.
- [x] **Add an "Expected Duration" column**, which can be optional or open-ended (e.g., "some time next week").
- [x] **Prompt the user for an expected duration** when adding a goal if they don’t specify one (but allow them to decline).

### **3️⃣ AI & Usability Improvements**
- [ ] **Handle edge cases** (e.g., a goal named "complete" should not confuse the system).
- [x] **Implement semantic goal identification**, so similar goals (e.g., "read a book" vs. "read any book") are recognized as the same.
- [x] **Make notes about the current status of a goal**, which the AI can process and provide feedback on.
- [x] **Implement local storage** for goals, so the user can access their goals privately offline.
- [ ] **Implement alternate LLMs** (e.g., local models) for more flexibility.
  - [x] **Implement alternate LLMs** using `liteLLM` - works for proprietary models, e.g., Claude.
  - [ ] **Implement local LLMs**.
- [ ] **Test the app's ability to edit and update goals** (e.g., changing name of a goal).
- [ ] **Allow user to modify spreadsheet schema** (e.g., add new columns for additional information).

### **4️⃣ User Experience & UI**
- [x] **Create a persistent view of the goal list**, instead of requiring the user to ask to view it each time.
- [ ] **Improve the logic for refreshing the goal list** after a new goal is added or an existing goal is updated.
- [x] **Display an initial welcome message** from the AI, describing the available functionality of the app.
- [ ] **Implement LLM-switching functionality** to allow users to switch between different models.

### **5️⃣ Debugging & Logging**
- [ ] **Create a logging system** to record every conversation during development for debugging purposes.

### **6️⃣ Codebase & Documentation**

### **7️⃣ Security & Privacy**
- [ ] **Implement authentication** (optional) for local CSV storage.

### **8️⃣ CLI**
- [ ] **Add command to print configuration** to the CLI.

## License

This project is licensed under the [GNU Affero General Public License](LICENSE) (AGPLv3).

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for review.
