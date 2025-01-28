import gspread
from oauth2client.service_account import ServiceAccountCredentials
import gradio as gr
from datetime import datetime

# Setup Google Sheets
def setup_google_sheets():
    # Define the scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Authenticate using the service account
    creds = ServiceAccountCredentials.from_json_keyfile_name("config/service_account.json", scope)
    client = gspread.authorize(creds)

    # Open the Google Sheet
    sheet = client.open("Squad Goals").sheet1  # Access the first sheet
    return sheet

# Log a new goal
def log_goal(goal):
    if not goal.strip():
        return "Goal cannot be empty!"
    
    try:
        sheet = setup_google_sheets()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([goal, "Pending", timestamp])
        return f"Goal '{goal}' logged successfully!"
    except Exception as e:
        return f"An error occurred: {e}"

# View all logged goals
def view_goals():
    try:
        sheet = setup_google_sheets()
        data = sheet.get_all_records()
        # Convert list of dictionaries to list of lists
        data_list = [[row["Goal"], row["Status"], row["Timestamp"]] for row in data]
        return data_list
    except Exception as e:
        return f"An error occurred: {e}"

# Mark a goal as completed
def mark_goal_complete(goal):
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
        return f"An error occurred: {e}"

# Gradio Interface
def squad_goals_app():
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
            view_button.click(view_goals, outputs=goal_table)
        
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
