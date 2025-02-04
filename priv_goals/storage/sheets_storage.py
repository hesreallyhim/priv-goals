

import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import List, Tuple
from priv_goals.constants import HEADER_NAMES
from priv_goals.storage.goal_storage import GoalStorage
from priv_goals.storage.goal import Goal

class GoogleSheetsStorage(GoalStorage):
    """Google Sheets implementation of goal storage.

    Implements the GoalStorage interface using Google Sheets as the backend.
    Handles authentication, connection management, and sheet operations.

    This implementation requires network connectivity and valid Google Sheets
    API credentials. All operations are subject to API quotas and rate limits.

    Attributes:
        credentials_path (str): Path to the Google Sheets API credentials file.
        sheet_name (str): Name of the Google Sheet used for storage.

    Example:
        >>> storage = GoogleSheetsStorage("credentials.json", "My Goals")
        >>> storage.log_goal("New project")
        'Goal "New project" logged successfully!'

    Note:
        - Requires valid Google Sheets API credentials
        - Network connectivity required for all operations
        - Subject to API quotas and rate limits
        - Handles OAuth2 authentication automatically
    """

    def __init__(self, credentials_path: str, sheet_name: str = "PRIV GOALS") -> None:
        """Initialize Google Sheets storage backend.

        Args:
            credentials_path (str): Path to service account JSON credentials.
            sheet_name (str, optional): Name of the Google Sheet to use.
                Defaults to "PRIV GOALS".

        Raises:
            RuntimeError: If Google Sheets setup fails.

        Example:
            >>> storage = GoogleSheetsStorage(
            ...     "service_account.json",
            ...     "Team Goals 2024"
            ... )
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
