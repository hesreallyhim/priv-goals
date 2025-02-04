"""Core application module for priv-goals."""

import json
import gradio as gr
from pathlib import Path
from typing import Dict, Any, List, Tuple

import litellm
from litellm import completion

from priv_goals.storage.goal import Goal
from priv_goals.utils.logger import Logger

from .storage import GoalStorage, CSVStorage, GoogleSheetsStorage
from .constants import HEADER_NAMES, SYSTEM_MESSAGE, WELCOME_MESSAGE, TOOLS

class PrivGoalsApp:
    """Main application class for priv-goals."""
    
    def __init__(self, storage: GoalStorage, llm_config: Dict[str, Any], logger: Logger):
        """Initialize the application.
        
        Args:
            storage: Storage backend instance
            llm_config: LLM configuration dictionary
            logger: Logger instance
        """
        self.storage = storage
        self.llm_config = llm_config
        self.messages = [SYSTEM_MESSAGE]
        
        # Update system message with initial goals
        initial_goals = storage.view_goals_formatted()[2]
        self.messages[0]["content"] += f"\n\nInitial goals:\n\n{initial_goals}"
        
        self.completion = self._completion
        self.logger = logger
    
    def _completion(self, **args):
        return completion(
            model=self.llm_config["model"],
            api_key=self.llm_config["api_key"],
            api_base=self.llm_config["api_base"],
            **args
        )
    
    def call_function(self, name: str, args: dict) -> str:
        """Execute the appropriate tool function based on the name."""
        self.logger.info(f"Tool call: {name} with args: {args}")
        functions = {
            "log_goal": lambda args: self.storage.log_goal(Goal(args["goal"])),
            "view_goals": lambda _: self.storage.view_goals_formatted()[2],
            "mark_goal_complete": lambda args: self.storage.mark_goal_complete(Goal(args["goal"])),
            "delete_goal": lambda args: self.storage.delete_goal(Goal(args["goal"])),
            # TODO: Debug this tool
            "update_goal_fields": lambda args: self.storage.update_goal_fields(args["goal"], args["updates"])
        }

        if name not in functions:
            raise ValueError(f"Unknown function: {name}")

        return functions[name](args)

    def chat_with_llm(self, user_message: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Handle interaction with the LLM and process tool calls."""
        try:
            # Add user message to messages
            self.messages.append({"role": "user", "content": user_message})
            
            # Get initial response
            response = self.completion(
                messages=self.messages,
                tools=TOOLS
            )
            
            response_message = response.choices[0].message
            self.logger.info(f"LLM response: {response_message}")
            
            # Handle tool calls if present
            if response_message.tool_calls:
                # Process tool calls
                self.messages.append({
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

                # Execute each tool call
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = self.call_function(function_name, function_args)
                    
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(function_response)
                    })

                # Get final response
                final_response = self.completion(
                    messages=self.messages,
                    tools=TOOLS
                )
                return final_response.choices[0].message.content, self.messages
            else:
                return response_message.content, self.messages
                
        except Exception as e:
            self.logger.error(f"Error during chat interaction: {e}")
            return "An error occurred. Please try again.", self.messages

    def create_interface(self) -> gr.Blocks:
        """Create and configure the Gradio interface."""
        with gr.Blocks(title="PRIV Goals") as interface:
            with gr.Row():
                # Goals display
                goals_dataframe = gr.Dataframe(
                    headers=HEADER_NAMES,
                    label="Your Goals",
                    value=self.storage.view_goals_formatted()[0],
                    interactive=False,
                    wrap=True
                )
            
            with gr.Row():
                chatbot = gr.Chatbot(
                    label="Priv Goals Chatbot",
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

            def interact(user_message: str, history: List) -> Tuple[List, str, List]:
                self.logger.info(f"User message: {user_message}")
                
                # Get response from LLM
                response, _ = self.chat_with_llm(user_message)
                
                # Update chat history
                history.append((user_message, response))
                
                # Update goals display
                updated_goals = self.storage.view_goals_formatted()[0]
                
                return history, "", updated_goals

            # Connect interface components
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

        return interface

def create_app(config: Dict[str, Any], debug: bool = False) -> gr.Blocks:
    """Create and configure the application.
    
    Args:
        config: Application configuration dictionary
        debug: Enable debug mode if True
    
    Returns:
        Configured Gradio Blocks interface
    """
    logger = Logger(
        log_dir=config["log_dir"] if "log_dir" in config else None,
        debug=debug,
        component="main"
    ).get_logger()
    
    if (debug):
        litellm._turn_on_debug()

    # Initialize storage backend
    if config["storage_type"] == "csv":
        storage = CSVStorage(Path.home() / ".priv-goals" / "goals.csv")
    else:
        storage = GoogleSheetsStorage(
            credentials_path=config["google_sheets_credentials"],
            sheet_name=config["google_sheets_name"]
        )

    # Create application instance
    app = PrivGoalsApp(
        storage=storage,
        llm_config={
            "model": config["model"],
            "api_key": config["api_key"],
            "api_base": config["api_base"]
        },
        logger=logger
    )

    return app.create_interface()
