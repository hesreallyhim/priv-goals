import gspread
from oauth2client.service_account import ServiceAccountCredentials
import gradio as gr
from datetime import datetime
from typing import List, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Setup Google Sheets
def setup_google_sheets() -> gspread.Worksheet:
    """
    Authenticate and connect to the Google Sheet.

    Returns:
        gspread.Worksheet: The first sheet of the Google Sheet.
    """
    try:
        # Define the scope
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

        # Add more detailed logging
        logging.info("Attempting to load credentials...")
        creds = ServiceAccountCredentials.from_json_keyfile_name("config/service_account.json", scope)
        
        logging.info("Authorizing with Google...")
        client = gspread.authorize(creds)
        
        logging.info("Opening spreadsheet...")
        sheet = client.open("SQUAD GOALS").sheet1  # Access the first sheet
        
        # Test access by trying to get the sheet title
        sheet_title = sheet.title
        logging.info(f"Successfully accessed sheet: {sheet_title}")
        
        return sheet
    except FileNotFoundError:
        logging.error("Service account JSON file not found at config/service_account.json")
        raise
    except ValueError as e:
        logging.error(f"Invalid service account JSON file: {e}")
        raise
    except Exception as e:
        logging.error(f"Error setting up Google Sheets: {str(e)}")
        logging.error(f"Error type: {type(e)}")
        raise

# Log a new goal
def log_goal(goal: str) -> str:
    """
    Log a new goal to the Google Sheet.

    Args:
        goal (str): The goal to log.

    Returns:
        str: A message indicating the result of the operation.
    """
    if not goal.strip():
        return "Goal cannot be empty!"
    
    try:
        sheet = setup_google_sheets()
        data = sheet.get_all_records()

        # Check for duplicates
        if any(row["Goal"] == goal for row in data):
            return f"Goal '{goal}' already exists!"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([goal, "Pending", timestamp])
        return f"Goal '{goal}' logged successfully!"
    except Exception as e:
        logging.error(f"Error logging goal: {e}")
        return "An unexpected error occurred. Please try again."

# View all logged goals
def view_goals() -> Union[List[List[str]], List[str]]:
    """
    Fetch all logged goals from the Google Sheet.

    Returns:
        Union[List[List[str]], List[str]]: A list of goals or an error message.
    """
    try:
        sheet = setup_google_sheets()
        data = sheet.get_all_records()

        # Convert list of dictionaries to list of lists
        data_list = [[row["Goal"], row["Status"], row["Timestamp"]] for row in data]
        return data_list
    except Exception as e:
        logging.error(f"Error fetching goals: {e}")
        return [["An unexpected error occurred while fetching goals."]]

# Mark a goal as completed
def mark_goal_complete(goal: str) -> str:
    """
    Mark a goal as completed in the Google Sheet.

    Args:
        goal (str): The goal to mark as completed.

    Returns:
        str: A message indicating the result of the operation.
    """
    try:
        sheet = setup_google_sheets()
        data = sheet.get_all_records()

        # Search for the goal
        for i, row in enumerate(data, start=2):  # Start at 2 to account for the header
            if row["Goal"] == goal and row["Status"] != "Completed":
                sheet.update_cell(i, 2, "Completed")  # Update "Status" column
                return f"Goal '{goal}' marked as completed!"
        
        return f"Goal '{goal}' not found or already completed."
    except Exception as e:
        logging.error(f"Error marking goal as completed: {e}")
        return "An unexpected error occurred. Please try again."

# Gradio Interface
def squad_goals_app() -> gr.Blocks:
    """
    Create the Gradio interface for the app.

    Returns:
        gr.Blocks: The Gradio Blocks interface.
    """
    with gr.Blocks() as app:
        gr.Markdown("## Squad Goals: Track Your Accomplishments")
        
        # Log Goal Section
        with gr.Row():
            goal_input = gr.Textbox(label="Enter a new goal")
            log_button = gr.Button("Log Goal")
            log_output = gr.Textbox(label="Log Output")
            log_button.click(log_goal, inputs=goal_input, outputs=log_output)
        
        # View Goals Section
        with gr.Row():
            view_button = gr.Button("View Goals")
            goal_table = gr.Dataframe(headers=["Goal", "Status", "Timestamp"], interactive=False)
            view_button.click(view_goals, outputs=goal_table, show_progress=True)
        
        # Mark Goal as Complete Section
        with gr.Row():
            complete_goal_input = gr.Textbox(label="Enter the goal to mark as completed")
            complete_button = gr.Button("Mark as Completed")
            complete_output = gr.Textbox(label="Completion Output")
            complete_button.click(mark_goal_complete, inputs=complete_goal_input, outputs=complete_output)
        
    return app

# Run the app
if __name__ == "__main__":
    app = squad_goals_app()
    app.launch()
