from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import logging
import gradio as gr

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env
load_dotenv()

# Retrieve the OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key is missing. Please set it in the .env file.")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Declare OpenAI model name
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# Setup Google Sheets
def setup_google_sheets() -> gspread.Worksheet:
    """
    Authenticate and connect to the Google Sheet.
    """
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("config/service_account.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("SQUAD GOALS").sheet1
        return sheet
    except Exception as e:
        logging.error(f"Error setting up Google Sheets: {e}")
        raise

def log_goal(goal: str) -> str:
    if not goal.strip():
        return "Goal cannot be empty!"
    try:
        sheet = setup_google_sheets()
        data = sheet.get_all_records()
        if any(row["Goal"] == goal for row in data):
            return f"Goal '{goal}' already exists!"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([goal, "Pending", timestamp])
        return f"Goal '{goal}' logged successfully!"
    except Exception as e:
        logging.error(f"Error logging goal: {e}")
        return "An unexpected error occurred. Please try again."

def view_goals() -> str:
    try:
        sheet = setup_google_sheets()
        data = sheet.get_all_records()
        if not data:
            return "No goals found."
        return "\n".join([f"- {row['Goal']} ({row['Status']})" for row in data])
    except Exception as e:
        logging.error(f"Error fetching goals: {e}")
        return "An unexpected error occurred while fetching goals."

def mark_goal_complete(goal: str) -> str:
    try:
        sheet = setup_google_sheets()
        data = sheet.get_all_records()
        for i, row in enumerate(data, start=2):  # Start at 2 for header
            if row["Goal"] == goal and row["Status"] != "Completed":
                sheet.update_cell(i, 2, "Completed")
                return f"Goal '{goal}' marked as completed!"
        return f"Goal '{goal}' not found or already completed."
    except Exception as e:
        logging.error(f"Error marking goal as completed: {e}")
        return "An unexpected error occurred. Please try again."

def delete_goal(goal: str) -> str:
    """
    Deletes a goal from the Google Sheets tracker.

    Args:
        goal (str): The name of the goal to delete.

    Returns:
        str: Success or error message.
    """
    try:
        sheet = setup_google_sheets()
        data = sheet.get_all_records()

        # Find the goal in the sheet
        for i, row in enumerate(data, start=2):  # Start at 2 to account for the header row
            if row["Goal"] == goal:
                sheet.delete_rows(i)
                return f"Goal '{goal}' has been deleted successfully."

        return f"Goal '{goal}' not found in the tracker."
    except Exception as e:
        logging.error(f"Error deleting goal: {e}")
        return "An unexpected error occurred. Please try again."

def view_goals_formatted() -> tuple[list, list]:
    """
    Returns goals in a formatted way for the DataFrame display.
    Returns tuple of (list of goals, list of column headers)
    """
    try:
        sheet = setup_google_sheets()
        data = sheet.get_all_records()
        if not data:
            return [], []
            
        # Format the data for display
        formatted_data = []
        for row in data:
            formatted_data.append([
                row['Goal'],
                row['Status'],
                row.get('Timestamp', '')
            ])
            
        headers = ['Goal', 'Status', 'Created At']
        return formatted_data, headers
    except Exception as e:
        logging.error(f"Error fetching formatted goals: {e}")
        return [], []

def should_refresh_goals(_messages: list) -> bool:
    """
    Checks if the most recent interaction included a tool call that modified the sheet.
    """
    # TODO: Implement a more robust check based on tool calls
    return True

# Define tools
tools = [{
    "type": "function",
    "function": {
        "name": "log_goal",
        "description": "Log a new goal to the system.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"}
            },
            "required": ["goal"]
        }
    }
}, {
    "type": "function",
    "function": {
        "name": "view_goals",
        "description": "View all logged goals.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}, {
    "type": "function",
    "function": {
        "name": "mark_goal_complete",
        "description": "Mark a goal as completed.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"}
            },
            "required": ["goal"]
        }
    }
}, {
    "type": "function",
    "function": {
        "name": "delete_goal",
        "description": "Delete a goal from the tracker.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {"type": "string"}
            },
            "required": ["goal"]
        }
    }
}]

def call_function(name: str, args: dict) -> str:
    """Executes the appropriate function based on the name."""
    functions = {
        "log_goal": log_goal,
        "view_goals": view_goals,
        "mark_goal_complete": mark_goal_complete,
        "delete_goal": delete_goal
    }
    
    if name in functions:
        return functions[name](**args) if args else functions[name]()
    else:
        raise ValueError(f"Unknown function: {name}")

def chat_with_openai(messages: list) -> tuple[str, list]:
    """
    Handles interaction with OpenAI API and processes tool calls if needed.
    """
    try:
        # Call OpenAI API
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools
        )

        response_message = completion.choices[0].message
        
        # Handle tool calls if present
        if response_message.tool_calls:
            # Append assistant's message with tool calls
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    for tool_call in response_message.tool_calls
                ]
            })

            # Process each tool call
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute the function
                function_response = call_function(function_name, function_args)
                
                # Append the tool response
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(function_response)
                })

            # Get final response from the model
            final_completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools
            )
            
            return final_completion.choices[0].message.content, messages
        else:
            # No tool call; respond directly
            return response_message.content, messages
            
    except Exception as e:
        logging.error(f"Error during chatbot interaction: {e}")
        return "An error occurred. Please try again.", messages

system_message = {
    "role": "system",
    "content": "You are a goal-tracking assistant that helps users manage their "
        "goals. You can help them add or delete goals, view existing goals, "
        "and mark goals as complete."
}

welcome_message = {
    "role": "assistant",
    "content": "# 🎯 Welcome to Squad Goals!\n"
        "I can help you track and manage your goals effectively. Here's what you can do:\n\n"
        "✅ **Add a new goal** – You can specify an optional completion date, or I'll ask if you have one in mind.\n"
        "✅ **View your active and completed goals** – I maintain a persistent view of your goal list.\n"
        "✅ **Mark a goal as completed** – I'll track when you started and completed it.\n"
        "✅ **Rename or delete a goal** – Keep your goals organized.\n"
        "✅ **Revert a completed goal back to \"in progress\"** – If you need to keep working on it.\n"
        "✅ **Add notes to a goal** – Keep track of updates, progress, or follow-up tasks.\n"
        "🔍 **I recognize similar goals** – I can help you avoid duplicates unless a previous goal has already been completed.\n"
        "📅 **I handle vague deadlines** – Tell me things like \"next week\" or \"by the end of the month,\" and I'll interpret it.\n\n"
        "💡 **Let's get started! What goal would you like to track today?** 🚀"
}

def gradio_app():
    # Initialize messages list
    messages = [system_message, welcome_message]
    
    with gr.Blocks() as app:
        with gr.Row():
            # Goals list display
            goals_dataframe = gr.Dataframe(
                headers=["Goal", "Status", "Created At"],
                label="Your Goals",
                value=view_goals_formatted()[0],
                interactive=False,
                wrap=True
            )
        
        with gr.Row():
            chatbot = gr.Chatbot(
                label="Squad Goals Chatbot",
                height=400,
                value=[[None, welcome_message["content"]]]
            )
        
        with gr.Row():
            input_box = gr.Textbox(
                label="Enter your message",
                placeholder="Type here...",
                scale=4
            )
            submit_button = gr.Button("Submit", scale=1)

        def refresh_goals():
            """Helper function to refresh the goals display"""
            goals_data, _ = view_goals_formatted()
            return goals_data

        def interact(user_message, history):
            if not user_message.strip():
                return history, "", None
                
            logging.info(f"User message: {user_message}")
            
            # Add user message to messages list
            messages.append({"role": "user", "content": user_message})
            
            # Get response from OpenAI
            response, updated_messages = chat_with_openai(messages)
            
            logging.info(f"Assistant response: {response}")
            
            # Update messages list
            messages[:] = updated_messages
            
            # Update chat history
            history.append((user_message, response))
            
            # Only refresh goals if a sheet-modifying tool was used
            updated_goals = refresh_goals() if should_refresh_goals(updated_messages) else None
            
            return history, "", updated_goals

        # Connect the interaction function
        submit_button.click(
            interact,
            inputs=[input_box, chatbot],
            outputs=[chatbot, input_box, goals_dataframe]
        )
        
        input_box.submit(
            interact,
            inputs=[input_box, chatbot],
            outputs=[chatbot, input_box, goals_dataframe]
        )

    return app

if __name__ == "__main__":
    app = gradio_app()
    app.launch()
