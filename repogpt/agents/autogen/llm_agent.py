import asyncio
import uuid
from typing import Dict, Union

from autogen import AssistantAgent
from autogen.agentchat.agent import Agent


class LLMAgent(AssistantAgent):
    def __init__(
        self, queue: asyncio.Queue, loop: asyncio.BaseEventLoop, *args, **kwargs
    ):
        self.queue = queue
        self.loop = loop
        super().__init__(*args, **kwargs)

    def _print_received_message(self, message: Union[Dict, str], sender: Agent):
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
        super()._print_received_message(message, sender)
