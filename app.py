from abc import ABC, abstractmethod
import csv
from datetime import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
import gradio as gr
import gspread
import litellm
from litellm import check_valid_key, completion, validate_environment
from oauth2client.service_account import ServiceAccountCredentials
# from openai import OpenAI

class LLMInitializationError(Exception):
    """Custom exception for LLM initialization errors"""
    pass

class DotEnvLoadingError(Exception):
    """Custom exception for .env loading errors"""
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env
if not load_dotenv():
    raise DotEnvLoadingError("Failed to load .env file from default path")

load_dotenv()

# Declare spreadsheet header names
HEADER_NAMES = ["Goal", "Status", "Created At", "Completed At", "Duration", "Expected Duration", "Notes"]
DEFAULT_OPENAI_MODEL_NAME = "gpt-4"

# Define tools
tools = [{
    "type": "function",
    "function": {
        "name": "log_goal",
        "description": "Add a new goal to the system.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "Name of the goal to add, or a phrase that is semantically equivalent."
                }
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
                "goal": {
                    "type": "string",
                    "description": "Name of the goal to add, or a phrase that is semantically equivalent."
                }
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
                "goal": {
                    "type": "string",
                    "description": "Name of the goal to add, or a phrase that is semantically equivalent."
                }
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
                    "description": "The name of the goal to update, or a semantically equivalent description."
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

def setup_completion_function(
    *args,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model_name: Optional[str] = None,
    stream: Optional[bool] = False,
    tools: Optional[List[Dict[str, Any]]] = tools,
    tool_choice: Optional[str] = "auto",
    **kwargs
):
    """
    Set up the completion function with the specified parameters.
    
    Args:
        stream: Whether to use streaming completions (optional - default: False)
        model_name: The model name to use for completions (optional - default: None)
    """
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    global completion
    def custom_completion(**kwargs):
        return litellm.completion(*args, stream=stream, model=model_name,api_key=api_key, base_url=api_base, tools=tools, tool_choice=tool_choice, **kwargs)
    completion = custom_completion

def initialize_lite_llm(
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    stream: Optional[bool] = False
) -> None:
    """
    Initialize LLM configuration and test the connection.
    Sets global litellm properties and tests the connection.
    Ensures that all required environment variables are set.
    Ensures that model supports tool-calling, and checks for parallel tool-calling.
    
    Args:
        api_base: Override API_BASE from env (optional)
        api_key: Override API_KEY from env (optional)
        model_name: Override LITE_LLM_MODEL_NAME from env (optional)
    
    Raises:
        LLMInitializationError: If initialization or connection test fails, or if LLM does not support tool-calling.
    """
    # Get configuration from environment or parameters
    # litellm.model = model_name or os.getenv('LITE_LLM_MODEL_NAME')
    LITE_LLM_MODEL_NAME = os.getenv("LITE_LLM_MODEL_NAME", DEFAULT_OPENAI_MODEL_NAME)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    api_key = api_key or os.getenv("LITE_LLM_API_KEY", OPENAI_API_KEY)
    api_base = api_base or os.getenv("LITE_LLM_API_BASE_URL", "https://api.openai.com/v1")
    model_name = model_name or LITE_LLM_MODEL_NAME
    
    # Comment or uncomment the following line to enable or disable liteLLM debug logs
    # litellm._turn_on_debug()
    
    # send requests to "ollama_chat", per liteLLM docs
    if model_name.startswith("ollama"):
        model_name = model_name.replace("ollama", "ollama_chat", 1)
    
    # Validate environment configuration
    keys_in_environment, missing_keys = validate_environment(model=model_name)
    if not keys_in_environment:
        raise LLMInitializationError("Invalid environment configuration, missing required keys: " + ", ".join(missing_keys))

    # Validate API key
    valid_key = check_valid_key(model=model_name, api_key=api_key)
    if not valid_key:
        raise LLMInitializationError(f"Invalid API key for model {model_name}")
    
    # Validate tool-calling support
    # if not litellm.supports_function_calling(model=model_name):
    #     raise LLMInitializationError(f"Model {model_name} does not support tool-calling")
    
    try:
        if not litellm.supports_function_calling(model=model_name):
            logging.warning(f"Model {model_name} does not support tool-calling")
            # raise LLMInitializationError(f"Model {model_name} does not support tool-calling")
        else:
            logging.info(f"Model {model_name} supports tool-calling")
    except Exception as e:
        logging.warning(f"Model {model_name} does not support tool-calling")
        # raise LLMInitializationError(f"Model {model_name} does not support tool-calling")
    
    supports_parallel_tool_calls = False
    
    # Check parallel function tool-calling support
    try:
        if not litellm.supports_parallel_function_calling(model=model_name):
            logging.warning(f"Model {model_name} does not support parallel function calls")
        else:
            supports_parallel_tool_calls=True
            logging.info(f"Model {model_name} supports parallel function calls")
    except Exception as e:
        logging.warning(f"Model {model_name} does not support parallel function calls")
    
    # Set up the completion function
    setup_completion_function(stream=stream, model_name=model_name, api_key=api_key, api_base=api_base, parallel_tools_calls=supports_parallel_tool_calls)
    
    # Test LLM connection
    test_response = completion(
        messages=[{"role": "user", "content": "Please respond with the string 'Pong'"}]
    )
    
    try:
        response_content = test_response.choices[0].message.content
        if "Pong" in response_content:
            print(
                f"Successfully initialized connection to {model_name}... "
                f"Test message = \"Ping\"... "
                f"Response = \"{response_content}\""
            )
        else:
            raise LLMInitializationError(f"Connection test message failed with response: {response_content}")
    except Exception as e:
        raise LLMInitializationError(f"Connection test message failed: {e}")

class Goal:
    """Encapsulates a goal with automatic sanitization for storage and clean display."""

    def __init__(self, name: str) -> None:
        # TODO: This is probably a symptom of a bug
        if isinstance(name, Goal):
            # Copy constructor
            self.display_name = name.display_name
            self.sanitized_name = name.sanitized_name
            return
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
    
    def strip(self) -> str:
        """Returns the sanitized goal name without the enclosing quotes."""
        logging.info("Goal strip method was invoked on: " + self.display_name)
        return self.display_name

class GoalStorage(ABC):
    """Abstract base class for goal storage backends."""

    @abstractmethod
    def log_goal(self, goal: str) -> str:
        """
        Logs a new goal into the system if it does not already exist.
        Use this to add a new goal to the system.

        Args:
            goal (str): The raw string representation of the goal to be logged, or a semantically equivalent phrase.

        Returns:
            str: A message indicating whether the goal was successfully logged or if it already exists.

        Raises:
            ValueError: If the goal string is empty or invalid.
        """
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
    
    @abstractmethod
    def update_goal_fields(self, goal_name: str, updates: dict) -> str:
        """
        Updates multiple fields for a goal.

        Args:
            storage (GoalStorage): The storage backend (GoogleSheetsStorage or CSVStorage).
            goal_name (str): The display name of the goal to update, or a phrase that is semantically equivalent.
            updates (dict): A dictionary where keys are field names and values are new values.

        Returns:
            str: Success or error message.
        """
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
    
    def view_goals_formatted(self) -> Tuple[List[List[str]], List[str], str]:
        """
        Returns goals in a formatted way for the DataFrame display and CSV representation.

        Returns:
            Tuple[List[List[str]], List[str], str]: (Formatted data for Gradio, Column headers, CSV string)
        """
        try:
            # TODO: Move common logic to a shared method
            data = self._load_goals()
            if not data:
                return [], [], "No goals found."

            formatted_data = [[row[header_name] for header_name in HEADER_NAMES] for row in data]

            csv_string = "\n".join([",".join(HEADER_NAMES)] + [",".join(map(str, row)) for row in formatted_data])
            logging.info("CSV Output:\n" + csv_string)

            return formatted_data, HEADER_NAMES, csv_string

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
        """
        Logs a new goal into the system if it does not already exist.

        Args:
            goal (str): The raw string representation of the goal to be logged.

        Returns:
            str: A message indicating whether the goal was successfully logged or if it already exists.

        Raises:
            ValueError: If the goal string is empty or invalid.

        Notes:
            - The goal is converted into a `Goal` object which sanitizes and formats the goal name.
            - The method checks for duplicates before logging the new goal.
            - The goal is stored with a status of "Pending" and a timestamp of when it was created.
        """
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
        Fetches and formats the goals data.

        This method loads the goals data, formats it into a list of lists based on predefined header names,
        and generates a CSV string representation of the data. If no data is found, it returns empty lists
        and a message indicating that no goals were found. In case of an error, it logs the error and returns
        an appropriate message. An AI assistant may use this method to view the current goals in CSV format
        by extracting the CSV string, which is the third element of the returned tuple.

        Returns:
            Tuple[List[List[str]], List[str], str]: A tuple containing:
                - A list of lists where each inner list represents a row of formatted goal data.
                - A list of header names used for formatting the data.
                - A CSV string representation of the formatted goal data.

        Raises:
            Exception: If an error occurs while fetching or formatting the goals data, it logs the error and
                       returns an empty list, an empty header list, and an error message.
        """
        try:
            # TODO: Move common logic to a shared method
            data = self._load_goals()
            if not data:
                return [], [], "No goals found."

            formatted_data = [[row[header_name] for header_name in HEADER_NAMES] for row in data]

            csv_string = "\n".join([",".join(HEADER_NAMES)] + [",".join(map(str, row)) for row in formatted_data])
            logging.info("CSV Output:\n" + csv_string)

            return formatted_data, HEADER_NAMES, csv_string

        except Exception as e:
            logging.error(f"Error fetching formatted goals: {e}")
            return [], [], "An unexpected error occurred while fetching goals."

    def mark_goal_complete(self, goal: Goal) -> str:
        """
        Marks the specified goal as completed.

        This method updates the status of the given goal to "Completed" and sets the 
        "Completed At" timestamp to the current date and time. It also calculates the 
        duration from the goal's creation to its completion.

        Args:
            goal (Goal): The name of the goal to be deleted, or a phrase that is semantically
                equivalent to the name.

        Returns:
            str: A message indicating whether the goal was successfully marked as completed 
             or if it was not found or already completed.
        """
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
        """
        Deletes a goal from the stored goals.

        Args:
            goal (Goal): The name of the goal to be deleted, or a phrase that is semantically
                equivalent to the name.

        Returns:
            str: A message indicating whether the goal was successfully deleted or not.
        """
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
            goal_name (str): The display name of the goal to update, or a phrase that is semantically equivalent.
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

        storage._save_goals(data)  # Save the updated data
        return f"Goal '{goal_name}' updated: " + ", ".join(f"{k} → {v}" for k, v in updates.items())
    
def should_refresh_goals(_messages: list) -> bool:
    """
    Checks if the most recent interaction included a tool call that modified the sheet.
    """
    # TODO: Implement a more robust check based on tool calls
    return True

def call_function(storage: GoalStorage, name: str, args: dict) -> str:
    """Executes the appropriate function based on the name."""
    logging.info(f"Tool call: {name} with args: {args}")
    functions = {
        "log_goal": lambda args: storage.log_goal(args["goal"]),
        "view_goals": lambda _: storage.view_goals_formatted()[2],
        "mark_goal_complete": lambda args: storage.mark_goal_complete(Goal(args["goal"])),
        "delete_goal": lambda args: storage.delete_goal(Goal(args["goal"])),
        "update_goal_fields": lambda args: storage.update_goal_fields(Goal(args["goal"]), args["updates"])
    }
    
    # functions = {
    #     "log_goal": storage.log_goal,
    #     "view_goals": storage.view_goals_formatted,
    #     "mark_goal_complete": storage.mark_goal_complete,
    #     "delete_goal": storage.delete_goal,
    #     "update_goal_fields": storage.update_goal_fields
    # }

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
        first_response = completion(
            # model=LITE_LLM_MODEL_NAME,
            messages=messages,
            # tools=tools
        )

        response_message = first_response.choices[0].message
        
        logging.info(f"First response message: {response_message}")
        
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
                    "name": function_name,
                    "content": str(function_response)
                })

            # Get final response from the model
            final_completion = completion(
                # model=LITE_LLM_MODEL_NAME,
                messages=messages,
                # tools=tools
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
        "Note that the user has a persistent view of the goals list as well. "
        "If the user asks you to make any modifications or updates to the list of goals, "
        "you may use one or more of the following tools: "
        "log_goal, view_goals, mark_goal_complete, delete_goal, update_goal_fields. "
        "If you do not invoke any of these tools, the goal-tracking system will not be updated, "
        "and the user will not see any changes to the goals list. "
        "After each interaction, inform the user of the actions you have taken."
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
    initial_goals = storage.view_goals_formatted()[2]
    # Initialize messages list
    SYSTEM_MESSAGE["content"] += "\n\n Initial goals:\n\n" + initial_goals + "\n\n" + "This message will be displayed at the start of the chat: " + WELCOME_MESSAGE["content"]
    messages = [SYSTEM_MESSAGE]
    
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
            # if not user_message.strip():
            #     return history, "", None
                
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
    # client = initialize_client()  # Use dynamically initialized client
    initialize_lite_llm()
    storage = initialize_storage() # Dynamically selects storage backend
    app = gradio_app(storage)
    app.launch()
