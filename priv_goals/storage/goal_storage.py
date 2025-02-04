from abc import ABC, abstractmethod
from typing import List

from priv_goals.storage.goal import Goal


class GoalStorage(ABC):
    """Abstract base class defining the interface for goal storage backends.

    This class establishes the contract that all goal storage implementations must
    follow. It provides a consistent interface for CRUD operations on goals,
    regardless of the underlying storage mechanism.

    The interface maintains separation between display names (user-facing) and
    sanitized names (storage-safe), with methods accepting display names but
    working with sanitized versions internally.

    Implementations must handle:
    - Goal creation and storage
    - Retrieval and formatting of goals
    - Status updates and completion tracking
    - Goal deletion
    - Field updates and metadata management

    Attributes:
        None

    Example:
        class MyStorageBackend(GoalStorage):
            def log_goal(self, goal: str) -> str:
                # Implementation here
                pass
    """

    @abstractmethod
    def log_goal(self, goal: str) -> str:
        """Creates and stores a new goal.

        Args:
            goal (str): The display name of the goal to store.

        Returns:
            str: Success or failure message.

        Raises:
            ValueError: If goal is empty or invalid.

        Example:
            >>> storage.log_goal("Learn Python")
            'Goal "Learn Python" logged successfully!'
        """
        pass

    @abstractmethod
    def view_goals_formatted(self) -> tuple[List[List[str]], List[str], str]:
        """Retrieves all goals in multiple formats for different use cases.

        Returns:
            tuple:
                - List[List[str]]: Matrix of goal data for display
                - List[str]: Column headers
                - str: CSV string representation

        Raises:
            Exception: If goal retrieval or formatting fails.

        Example:
            >>> data, headers, csv_str = storage.view_goals_formatted()
            >>> print(headers)
            ['Goal', 'Status', 'Created At', ...]
        """
        pass
    
    @abstractmethod
    def mark_goal_complete(self, goal: Goal) -> str:
        """Updates a goal's status to completed.

        Args:
            goal (Goal): The goal to mark complete.

        Returns:
            str: Success message or not found/already complete message.

        Example:
            >>> storage.mark_goal_complete(Goal("Learn Python"))
            'Goal "Learn Python" marked as completed!'
        """
        pass

    @abstractmethod
    def delete_goal(self, goal: Goal) -> str:
        """Removes a goal from storage.

        Args:
            goal (Goal): The goal to delete.

        Returns:
            str: Success message or not found message.

        Example:
            >>> storage.delete_goal(Goal("Abandoned Task"))
            'Goal "Abandoned Task" has been deleted successfully.'
        """
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
