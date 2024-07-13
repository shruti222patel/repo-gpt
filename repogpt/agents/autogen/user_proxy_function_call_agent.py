import asyncio
import json
import logging
import uuid
from typing import Dict, Union

import autogen
from autogen.agentchat.agent import Agent

try:
    from termcolor import colored
except ImportError:

    def colored(x, *args, **kwargs):
        return x


logger = logging.getLogger(__name__)


class UserProxyFunctionCallAgent(autogen.UserProxyAgent):
    def __init__(
        self, queue: asyncio.Queue, loop: asyncio.BaseEventLoop, *args, **kwargs
    ):
        self.queue = queue
        self.loop = loop
        super().__init__(*args, **kwargs)

    def _print_received_message(self, message: Union[Dict, str], sender: Agent):
        if message != "" and message.get("content", None) is not None:
            asyncio.run_coroutine_threadsafe(
                self.queue.put(
                    {
                        "message": message.get("content", ""),
                        "sender": sender.name,
                        "correlation_id": str(uuid.uuid4()),
                    }
                ),
                self.loop,
            )
        else:
            # Whenever there is a funtion call the message is None, setting this to sender_name so it can be used in the execute_function method
            self.sender_name = sender.name
        super()._print_received_message(message, sender)

    def execute_function(self, func_call):
        """Execute a function call and return the result.

        Override this function to modify the way to execute a function call.

        Args:
            func_call: a dictionary extracted from openai message at key "function_call" with keys "name" and "arguments".

        Returns:
            A tuple of (is_exec_success, result_dict).
            is_exec_success (boolean): whether the execution is successful.
            result_dict: a dictionary with keys "name", "role", and "content". Value of "role" is "function".
        """
        func_name = func_call.get("name", "")

        message = (
            f"Searching codebase for {func_call.get('arguments')}..."
            if func_call.get("arguments", False)
            else "Searching codebase..."
        )

        asyncio.run_coroutine_threadsafe(
            self.queue.put(
                {
                    "message": message,
                    "sender": self.sender_name,
                    "correlation_id": str(uuid.uuid4()),
                }
            ),
            self.loop,
        )

        func = self._function_map.get(func_name, None)

        if hasattr(func, "__self__"):
            func = getattr(self, func_name, None)

        is_exec_success = False
        if func is not None:
            # Extract arguments from a json-like string and put it into a dict.
            input_string = self._format_json_str(func_call.get("arguments", "{}"))
            try:
                arguments = json.loads(input_string)
            except json.JSONDecodeError as e:
                arguments = None
                content = f"Error: {e}\n You argument should follow json format."

            # Try to execute the function
            if arguments is not None:
                print(
                    colored(f"\n>>>>>>>> EXECUTING FUNCTION {func_name}...", "magenta"),
                    flush=True,
                )
                try:
                    content = func(**arguments)
                    is_exec_success = True
                except Exception as e:
                    content = f"Error: {e}"
                    print(e)
                    raise e
                # print(f"Finished executing, here is the content: {content}")
                # print(f"is_exec_success: {is_exec_success}")
        else:
            content = f"Error: Function {func_name} not found."

        return is_exec_success, {
            "name": func_name,
            "role": "function",
            "content": str(content),
        }
