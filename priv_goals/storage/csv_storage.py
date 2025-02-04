import csv
from datetime import datetime
import logging
import os
from typing import Dict, List, Tuple
from priv_goals.constants import HEADER_NAMES
from priv_goals.storage.goal_storage import GoalStorage
from priv_goals.storage.goal import Goal

# TODO/FIXME: Use consistent typing (Goal vs. str) for goal arguments

class CSVStorage(GoalStorage):
    """CSV file-based implementation of goal storage.

    Implements the GoalStorage interface using a CSV file as the backend.
    Handles file creation, reading, writing, and maintains proper CSV formatting
    and header structure.

    The implementation is synchronous and involves file I/O for all operations.
    Consider file locking for multi-process scenarios.

    Attributes:
        csv_path (str): Path to the CSV storage file.

    Example:
        >>> storage = CSVStorage("~/.priv_goals/goals.csv")
        >>> storage.log_goal("New project")
        'Goal "New project" logged successfully!'

    Note:
        - Creates CSV with headers if file doesn't exist
        - All operations are atomic file reads/writes
        - No built-in concurrency control
    """

    def __init__(self, csv_path: str):
        """Initialize CSV storage backend.

        Args:
            csv_path (str): Path for CSV storage. User directory symbols (~)
                are expanded.

        Raises:
            OSError: If path is invalid or file operations fail.

        Example:
            >>> storage = CSVStorage("~/.priv_goals/goals.csv")
        """
        self.csv_path = os.path.expanduser(csv_path)
        self._ensure_csv_file()

    def _ensure_csv_file(self) -> None:
        """Creates the CSV file with headers if it does not exist."""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(HEADER_NAMES)

    def _load_goals(self) -> List[Dict]:
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
