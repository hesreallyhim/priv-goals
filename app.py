from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import logging
import gradio as gr
from abc import ABC, abstractmethod
from typing import List, Tuple
import csv

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

# Declare spreadsheet header names
HEADER_NAMES = ["Goal", "Status", "Created At", "Completed At", "Duration", "Expected Duration", "Notes"]

class Goal:
    """Encapsulates a goal with automatic sanitization for storage and clean display."""

    def __init__(self, name: str):
        self.display_name: str = name.strip()  # Store original user input
        self.sanitized_name: str = self._sanitize_goal_name(self.display_name)  # Store sanitized version

    def _sanitize_goal_name(self, goal: str) -> str:
        """
        Prevents spreadsheet formula execution by enclosing in single quotes.

        NOTE:
        - This ensures security but means that the stored value in raw data (CSV/Google Sheets)
          will include quotes (e.g., `'Read a book'`).
        - Users might expect to see their input exactly as entered when viewing raw data.
        """
        if not goal:
            raise ValueError("Goal name cannot be empty.")
        
        return f"'{goal}'"  # Always wrap in single quotes

class GoalStorage(ABC):
    """Abstract base class for goal storage backends."""

    @abstractmethod
    def log_goal(self, goal: str) -> str:
        """Logs a new goal. Accepts raw user input (`str`), then converts it to a `Goal` object internally."""
        pass

    @abstractmethod
    def view_goals_formatted(self) -> tuple[List[List[str]], List[str], str]:
        """Retrieves all goals as a formatted CSV string."""
        pass
    
    @abstractmethod
    def mark_goal_complete(self, goal: Goal) -> str:
        """Marks a goal as completed. Expects a sanitized `Goal` object."""
        pass

    @abstractmethod
    def delete_goal(self, goal: Goal) -> str:
        """Deletes a goal. Expects a sanitized `Goal` object."""
        pass

class GoogleSheetsStorage(GoalStorage):
    """Google Sheets-based storage for goal tracking."""

    def __init__(self, credentials_path: str, sheet_name: str = "SQUAD GOALS") -> None:
        """
        Initializes the Google Sheets storage.

        Args:
            credentials_path (str): Path to the service account JSON file.
            sheet_name (str, optional): Name of the Google Sheet. Defaults to "SQUAD GOALS".
        """
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name

    def _setup_google_sheets(self) -> gspread.Worksheet:
        """
        Authenticates and connects to the Google Sheet.

        Returns:
            gspread.Worksheet: The first worksheet of the specified Google Sheet.
        """
        try:
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_path, scope)
            client = gspread.authorize(creds)
            sheet = client.open(self.sheet_name).sheet1
            return sheet
        except Exception as e:
            raise RuntimeError(f"Error setting up Google Sheets: {e}")

    def log_goal(self, goal: str) -> str:
        goal_obj: Goal = Goal(goal)  # Convert raw string to Goal

        # sheet: gspread.Worksheet = self._setup_google_sheets()
        # data: List[dict] = sheet.get_all_records()
        
        sheet = self._setup_google_sheets()
        data = sheet.get_all_records()

        if any(row["Goal"] == goal_obj.sanitized_name for row in data):
            return f"Goal '{goal_obj.display_name}' already exists!"

        timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([goal_obj.sanitized_name, "Pending", timestamp])

        return f"Goal '{goal_obj.display_name}' logged successfully!"
    
    def view_goals_formatted(self) -> tuple[List[List[str]], List[str], str]:
        """
        Returns goals in a formatted way for the DataFrame display.
        Returns CSV-formatted data and headers.
        """
        try:
            sheet = self._setup_google_sheets()
            data = sheet.get_all_records()
            if not data:
                return [], [], "No goals found."
                
            # Format the data for display
            formatted_data = []
            for row in data:
                formatted_data.append([
                    row['Goal'],
                    row['Status'],
                    row['Created At']
                ])
                
            headers = ['Goal', 'Status', 'Created At']
            csv = "\n".join([",".join(headers)] + [",".join(map(str, row)) for row in formatted_data])
            logging.info("csv: " + csv)
            return formatted_data, headers, csv
        except Exception as e:
            logging.error(f"Error fetching formatted goals: {e}")
            return [], [], "An unexpected error occurred while fetching goals."

    def mark_goal_complete(self, goal: Goal) -> str:
        sheet: gspread.Worksheet = self._setup_google_sheets()
        data: List[dict] = sheet.get_all_records()

        for i, row in enumerate(data, start=2):  # Start at 2 for header
            if row["Goal"] == goal.sanitized_name and row["Status"] != "Completed":
                sheet.update_cell(i, 2, "Completed")
                return f"Goal '{goal.display_name}' marked as completed!"

        return f"Goal '{goal.display_name}' not found or already completed."

    def delete_goal(self, goal: Goal) -> str:
        sheet: gspread.Worksheet = self._setup_google_sheets()
        data: List[dict] = sheet.get_all_records()

        for i, row in enumerate(data, start=2):
            if row["Goal"] == goal.sanitized_name:
                sheet.delete_rows(i)
                return f"Goal '{goal.display_name}' has been deleted successfully."

        return f"Goal '{goal.display_name}' not found."


class CSVStorage(GoalStorage):
    """CSV-based storage for goal tracking."""

    def __init__(self, csv_path: str):
        """
        Initializes the CSV storage.

        Args:
            csv_path (str): Path to the CSV file.
        """
        self.csv_path = os.path.expanduser(csv_path)
        self._ensure_csv_file()

    def _ensure_csv_file(self) -> None:
        """Creates the CSV file with headers if it does not exist."""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(HEADER_NAMES)

    def _load_goals(self) -> List[dict]:
        """Loads goals from the CSV file into a list of dictionaries."""
        if not os.path.exists(self.csv_path):
            return []

        with open(self.csv_path, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            return list(reader)

    def _save_goals(self, data: List[dict]) -> None:
        """Writes updated goal data back to the CSV file."""
        with open(self.csv_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=HEADER_NAMES)
            writer.writeheader()
            writer.writerows(data)

    def log_goal(self, goal: str) -> str:
        goal_obj = Goal(goal)  # Convert raw string to `Goal`
        data = self._load_goals()

        # TODO: Identifying duplicates should be handled by the assistant
        if any(row["Goal"] == goal_obj.sanitized_name for row in data):
            return f"Goal '{goal_obj.display_name}' already exists!" 

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data.append({
            "Goal": goal_obj.sanitized_name,
            "Status": "Pending",
            "Created At": timestamp,
            "Completed At": "",
            "Duration": "",
            "Expected Duration": "",
            "Notes": ""
        })

        self._save_goals(data)
        return f"Goal '{goal_obj.display_name}' logged successfully!"

    def view_goals_formatted(self) -> Tuple[List[List[str]], List[str], str]:
        """
        Returns goals in a formatted way for the DataFrame display and CSV representation.

        Returns:
            Tuple[List[List[str]], List[str], str]: (Formatted data for Gradio, Column headers, CSV string)
        """
        try:
            data = self._load_goals()
            if not data:
                return [], [], "No goals found."

            formatted_data = [[row[header_name] for header_name in HEADER_NAMES] for row in data]
            headers = HEADER_NAMES

            csv_string = "\n".join([",".join(headers)] + [",".join(map(str, row)) for row in formatted_data])
            logging.info("CSV Output:\n" + csv_string)

            return formatted_data, headers, csv_string

        except Exception as e:
            logging.error(f"Error fetching formatted goals: {e}")
            return [], [], "An unexpected error occurred while fetching goals."

    def mark_goal_complete(self, goal: Goal) -> str:
        data = self._load_goals()
        updated = False

        for row in data:
            if row["Goal"] == goal.sanitized_name and row["Status"] != "Completed":
                row["Status"] = "Completed"
                row["Completed At"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if row["Completed At"]:
                    row["Duration"] = str(datetime.strptime(row["Completed At"], "%Y-%m-%d %H:%M:%S") - datetime.strptime(row["Created At"], "%Y-%m-%d %H:%M:%S"))
                updated = True
                break

        if not updated:
            return f"Goal '{goal.display_name}' not found or already completed."

        self._save_goals(data)
        return f"Goal '{goal.display_name}' marked as completed!"

    def delete_goal(self, goal: Goal) -> str:
        data = self._load_goals()
        new_data = [row for row in data if row["Goal"] != goal.sanitized_name]

        if len(new_data) == len(data):
            return f"Goal '{goal.display_name}' not found."

        self._save_goals(new_data)
        return f"Goal '{goal.display_name}' has been deleted successfully."
    
    def update_goal_fields(storage: GoalStorage, goal_name: str, updates: dict) -> str:
        """
        Updates multiple fields for a goal.

        Args:
            storage (GoalStorage): The storage backend (GoogleSheetsStorage or CSVStorage).
            goal_name (str): The display name of the goal to update.
            updates (dict): A dictionary where keys are field names and values are new values.

        Returns:
            str: Success or error message.
        """
        # Validate fields
        invalid_fields = [field for field in updates.keys() if field not in HEADER_NAMES]
        if invalid_fields:
            return f"Invalid fields: {', '.join(invalid_fields)}. Allowed fields: {', '.join(HEADER_NAMES)}"

        data = storage._load_goals()
        updated = False

        for row in data:
            if row["Goal"] == Goal(goal_name).sanitized_name:
                for field_name, new_value in updates.items():
                    row[field_name] = new_value  # ✅ Update each specified field
                updated = True
                break

        if not updated:
            return f"Goal '{goal_name}' not found."

        storage._save_goals(data)  # ✅ Save the updated data
        return f"Goal '{goal_name}' updated: " + ", ".join(f"{k} → {v}" for k, v in updates.items())
    
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
}, {
    "type": "function",
    "function": {
        "name": "update_goal_fields",
        "description": "Update multiple fields for a goal.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "The name of the goal to update."
                },
                "updates": {
                    "type": "object",
                    "description": "A dictionary of fields to update. Keys are field names, values are new values."
                }
            },
            "required": ["goal", "updates"]
        }
    }
}]

def call_function(storage: GoalStorage, name: str, args: dict) -> str:
    """Executes the appropriate function based on the name."""
    functions = {
        "log_goal": lambda args: storage.log_goal(args["goal"]),
        "view_goals": lambda _: storage.view_goals_formatted()[2],
        "mark_goal_complete": lambda args: storage.mark_goal_complete(Goal(args["goal"])),
        "delete_goal": lambda args: storage.delete_goal(Goal(args["goal"])),
        "update_goal_fields": lambda args: storage.update_goal_fields(Goal(args["goal"]), args["updates"])
    }

    if name not in functions:
        raise ValueError(f"Unknown function: {name}")

    return functions[name](args)

def chat_with_openai(storage: GoalStorage, messages: list) -> tuple[str, list]:
    """
    Handles interaction with OpenAI API and processes tool calls if needed.

    Args:
        storage (GoalStorage): The storage backend (GoogleSheetsStorage or CSVStorage).
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
                function_args = json.loads(tool_call.function.arguments) # TODO: Validate arguments
                
                # Execute the function
                function_response = call_function(storage, function_name, function_args)
                
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

SYSTEM_MESSAGE = {
    "role": "system",
    "content": "You are a goal-tracking assistant that helps users manage their "
        "goals. You can help them add or delete goals, view existing goals, "
        "track the completion status of goals, manage notes for each goal, "
        "and track the expected and actual duration of each goal. "
        "When the user asks you to add a goal, you should ensure that you understand "
        "the user's intention sufficiently such that you can assign the goal a unique or descriptor, "
        "and see if the user has an expected completion date in mind "
        "(the date is optional and may be vague). "
        "When helping the user, make sure you clearly "
        "understand their intentions and what they want you to do. "
        "Unless the user tells you very specifically which goal they are referring to, "
        "and refers to it by its literal wording, follow the guidelines below: "
        "You should differentiate between goals that are somewhat similar, but "
        "not the same, such as 'read a book' and 'read a book every day', "
        "or, 'read a book' and 'write a book'. "
        "Also, you should recognize that goals like completing a book and finishing a book "
        "are the same, even though they are worded slightly differently. "
        "If you're not sure what the user wants to achieve, or "
        "which goal they are referring to, ask for clarification. "
        "Note that the user has a persistent view of the goals list as well."
}

WELCOME_MESSAGE = {
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

def initialize_storage() -> GoalStorage:
    """
    Dynamically initializes the storage backend based on environment configuration.
    
    Returns:
        GoalStorage: An instance of the selected storage backend.
    """
    storage_type = os.getenv("STORAGE_BACKEND", "csv").lower()

    if storage_type == "google_sheets":
        credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "config/service_account.json")
        sheet_name = os.getenv("GOOGLE_SHEETS_NAME", "SQUAD GOALS")
        logging.info(f"Using Google Sheets storage: {sheet_name}")
        return GoogleSheetsStorage(credentials_path, sheet_name)

    elif storage_type == "csv":
        csv_dir = os.path.expanduser("~/.priv_goals")  # Use private directory for CSV storage
        os.makedirs(csv_dir, exist_ok=True)  # Ensure directory exists

        csv_path = os.path.join(csv_dir, "goals.csv")

        # Ensure the CSV file exists and has the correct headers
        # TODO: Conflict resolution if the headers are incorrect
        if not os.path.exists(csv_path):
            with open(csv_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(HEADER_NAMES)  # Use the standard header names

        logging.info(f"Using CSV storage: {csv_path}")
        return CSVStorage(csv_path)

    else:
        raise ValueError(f"Invalid STORAGE_BACKEND: {storage_type}. Choose 'google_sheets' or 'csv'.")

def gradio_app(storage: GoalStorage) -> gr.Interface:
    # Initialize messages list
    messages = [SYSTEM_MESSAGE, WELCOME_MESSAGE]
    
    with gr.Blocks() as app:
        with gr.Row():
            # Goals Dataframe display
            formatted_goals = storage.view_goals_formatted()
            goals_dataframe = gr.Dataframe(
                headers=HEADER_NAMES,
                label="Your Goals",
                value=formatted_goals[0],
                interactive=False,
                wrap=True
            )
        
        with gr.Row():
            chatbot = gr.Chatbot(
                label="Squad Goals Chatbot",
                height=400,
                value=[[None, WELCOME_MESSAGE["content"]]]
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
            goals_data = storage.view_goals_formatted()[0]
            logging.info(f"Goals data: {goals_data}")
            return goals_data

        def interact(user_message, history):
            if not user_message.strip():
                return history, "", None
                
            logging.info(f"User message: {user_message}")
            
            # Add user message to messages list
            messages.append({"role": "user", "content": user_message})
            
            # Get response from OpenAI
            response, updated_messages = chat_with_openai(storage, messages)
            
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
    storage = initialize_storage() # Dynamically selects storage backend
    app = gradio_app(storage)
    app.launch()
