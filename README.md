
# Squad Goals

**Squad Goals** is a simple goal-tracking app that allows users to:
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
   cd squad-goals
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
squad-goals/
├── config/                   # Configuration files (e.g., service account JSON)
├── app.py                    # Main application logic
├── requirements.txt          # Python dependencies
├── .env                      # Local environment variables (optional)
├── .env.example              # Example environment file
├── .gitignore                # Git ignore rules
└── README.md                 # Project documentation
```

## Future Work

1. **Enhance the User Experience (UX)**:
   - Add validation feedback and success messages.
   - Display notifications upon successful actions.

2. **Data Filters**:
   - Enable filtering of goals by status (e.g., `Pending` or `Completed`).

3. **Analytics and Insights**:
   - Track goal completion metrics (e.g., percentage completed, time-to-completion trends).
   - Add simple visualizations (e.g., progress charts).

4. **Extended Functionality**:
   - Add priority levels for goals (e.g., `High`, `Medium`, `Low`).
   - Implement due dates and reminders for goals.

5. **Export/Import Options**:
   - Allow exporting goals to CSV or JSON.
   - Enable importing existing data.

6. **Deployment**:
   - Host the app on a platform like Hugging Face Spaces, AWS, or Heroku.

## Roadmap

### **1️⃣ Goal Management Enhancements**
- [x] **Delete/remove goals** from the tracker.
- [ ] **Rename goals** for better organization.
- [ ] **Revert a completed goal back to "in progress."**
- [ ] **Allow users to enter a duplicate goal** (e.g., "read a book") if a similar goal was previously completed.
- [ ] **Allow the user to "un-delete" a goal** that was removed by mistake.

### **2️⃣ Time Tracking & Scheduling**
- [ ] **Track timestamps**: When a goal is created, when it is completed, and how long it took.
- [ ] **Calculate and display average completion time** for goals.
- [ ] **Add an "Intended Completion Date" column**, which can be optional or open-ended (e.g., "some time next week").
- [ ] **Prompt the user for a completion date** when adding a goal if they don’t specify one (but allow them to decline).

### **3️⃣ AI & Usability Improvements**
- [ ] **Handle edge cases** (e.g., a goal named "complete" should not confuse the system).
- [ ] **Implement semantic goal identification**, so similar goals (e.g., "read a book" vs. "read any book") are recognized as the same.
- [ ] **Make notes about the current status of a goal**, which the AI can process and provide feedback on.
- [ ] **Implement local storage** for goals, so the user can access their goals privately offline.
- [ ] **Implement alternate LLMs** (e.g., local models) for more flexibility.

### **4️⃣ User Experience & UI**
- [x] **Create a persistent view of the goal list**, instead of requiring the user to ask to view it each time.
- [ ] **Improve the logic for refreshing the goal list** after a new goal is added or an existing goal is updated.
- [x] **Display an initial welcome message** from the AI, describing the available functionality of the app.

### **5️⃣ Debugging & Logging**
- [ ] **Create a logging system** to record every conversation during development for debugging purposes.

### **6️⃣ Codebase & Documentation**
- [ ] **Rename project** to `priv-goals`

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for review.
