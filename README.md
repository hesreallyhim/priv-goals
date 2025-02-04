
# Priv Goals

**Priv Goals** is a simple goal-tracking app that allows users to:
- Log new goals with a status of "Pending."
- View a list of all logged goals along with their statuses and timestamps.
- Mark goals as "Completed."

The app uses **Gradio** for the user interface and **Google Sheets** as the backend for data persistence.

## Features

1. Log a new goal.
2. View all logged goals in a table format.
3. Mark a specific goal as "Completed."

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd priv-goals
   ```

2. **Set up the virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Google Sheets API**:
   - Create a service account in Google Cloud and download the credentials file.
   - Place the file in the `config/` directory and name it `service_account.json`.
   - Share your Google Sheet with the service account email and grant **Editor** access.

5. **Run the app**:
   ```bash
   python app.py
   ```

## Usage

- Open the Gradio interface in your browser.
- Talk to the chatbot to log new goals, view existing goals, and mark goals as completed.

## Project Structure

```
priv-goals/
├── config/                   # Configuration files (e.g., service account JSON)
├── app.py                    # Main application logic
├── requirements.txt          # Python dependencies
├── .env                      # Local environment variables (optional)
├── .env.example              # Example environment file
├── .gitignore                # Git ignore rules
└── README.md                 # Project documentation
```

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
- [ ] **Rename project** to `priv-goals`

### **7️⃣ Security & Privacy**
- [ ] **Implement authentication** (optional) for local CSV storage.

## License

This project is licensed under the [GNU Affero General Public License](LICENSE).

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for review.
