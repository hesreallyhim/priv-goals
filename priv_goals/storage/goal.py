class Goal:
    """Represents a user goal with sanitized storage and display formatting.

    This class manages the dual representation of goals - a user-friendly display version
    and a storage-safe sanitized version. It handles sanitization to prevent security issues
    like formula injection in spreadsheet storage while maintaining readable output for users.

    Attributes:
        display_name (str): The original goal name as entered by the user.
        sanitized_name (str): Storage-safe version of the goal name, wrapped in quotes.

    Example:
        >>> goal = Goal("Complete project by Friday")
        >>> print(goal.display_name)
        'Complete project by Friday'
        >>> print(goal.sanitized_name)
        "'Complete project by Friday'"

    Note:
        The class includes a copy constructor pattern that should be reviewed as it may
        indicate architectural issues in the codebase.
    """

    def __init__(self, name: str) -> None:
        """Initialize a new Goal instance.

        Args:
            name (str): The goal name or description to store.

        Raises:
            ValueError: If name is empty, None, or not a string.
            TypeError: If name is a Goal instance (indicates potential code issue).

        Example:
            >>> goal = Goal("Read War and Peace")
            >>> print(goal.display_name)
            Read War and Peace
        """
        if isinstance(name, Goal):
            # Copy constructor pattern - may indicate design issues
            self.display_name = name.display_name
            self.sanitized_name = name.sanitized_name
            return
        
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Goal name must be a non-empty string")
        
        self.display_name = name.strip()
        self.sanitized_name = self._sanitize_goal_name(self.display_name)

    def _sanitize_goal_name(self, goal_display_name: str) -> str:
        """Sanitizes the goal name for safe storage.

        Wraps the goal name in single quotes to prevent formula injection in
        spreadsheet storage systems. This ensures the content is treated as
        literal text rather than potentially executable formulas.

        Args:
            goal_display_name (str): The display name of the goal to sanitize.

        Returns:
            str: The sanitized goal name, wrapped in single quotes.

        Raises:
            ValueError: If goal is empty or None.

        Example:
            >>> goal = Goal("=SUM(A1:A10)")  # Potentially unsafe formula
            >>> print(goal.sanitized_name)
            "'=SUM(A1:A10)'"  # Safely stored as text
        """
        if not goal_display_name:
            raise ValueError("Goal name cannot be empty.")
        
        return f"'{goal_display_name}'"

    def strip(self) -> str:
        """Returns the display version of the goal name.

        Provides string-like behavior for compatibility with code expecting
        string objects. Returns the human-readable display_name rather than
        the sanitized version.

        Returns:
            str: The unsanitized display name of the goal.

        Example:
            >>> goal = Goal("My Goal")
            >>> print(goal.strip())
            'My Goal'
        """
        return self.display_name
