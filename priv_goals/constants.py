"""Shared constants for the priv-goals application."""

from pathlib import Path

DEFAULT_LOG_DIR = Path.home() / ".priv-goals" / "logs"

# Storage constants
HEADER_NAMES = ["Goal", "Status", "Created At", "Completed At", "Duration", "Expected Duration", "Notes"]

# System prompts
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
    "content": "# 🎯 Welcome to Priv Goals!\n"
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

# Tool definitions
TOOLS = [{
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
