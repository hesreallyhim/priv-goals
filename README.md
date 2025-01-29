
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

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for review.
