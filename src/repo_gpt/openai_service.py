# Set your OpenAI API key as an environment variable
import json
import logging
import os

import numpy as np
import openai as openai
import tiktoken
from openai import OpenAI
from tenacity import (  # for exponential backoff
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from repo_gpt.utils import Singleton

MAX_RETRIES = 3
GPT_MODEL = "gpt-3.5-turbo"  # "gpt-3.5-turbo-16k"
EMBEDDING_MODEL = "text-embedding-ada-002"
TEMPERATURE = (
    0.4  # temperature = 0 can sometimes get stuck in repetitive loops, so we use 0.4
)

logger = logging.getLogger(__name__)


def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warn("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = (
            4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        )
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        logger.warn(
            "Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613."
        )
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        logger.warn(
            "Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613."
        )
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(json.dumps(value)))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def tokens_from_string(string, model="gpt-3.5-turbo"):
    """Return the number of tokens used by a string."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warn("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(string)

    return tokens


def num_tokens_from_string(prompt, model="gpt-3.5-turbo"):
    """Return the number of tokens used by a string."""
    return len(tokens_from_string(prompt, model=model))


def handle_after_retry(retry_state):
    if retry_state.attempt_number < 6:
        print(f"Attempt {retry_state.attempt_number} failed. Retrying...")
        pass
    else:
        # Log or print if final attempt also fails
        print(f"Final attempt failed after {retry_state.attempt_number} retries.")


class OpenAIService(metaclass=Singleton):
    GENERAL_SYSTEM_PROMPT = "You are a world-class software engineer and technical writer specializing in understanding code + architecture + tradeoffs and explaining them clearly and in detail. You are helpful and answer questions the user asks. You organize your explanations in easy to read markdown."
    ANALYSIS_SYSTEM_PROMPT = "You are a world-class developer with an eagle eye for unintended bugs and edge cases. You carefully explain code with great detail and accuracy. You organize your explanations in markdown-formatted, bulleted lists."

    def __init__(self, openai_api_key: str | None = None):
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def get_answer(
        self, query: str, code: str, system_prompt: str = GENERAL_SYSTEM_PROMPT
    ):
        query = f"""Use the code below to answer the subsequent question. If the answer cannot be found, write "I don't know."
        ```
        {code}
        ```
        Question: {query}"""

        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": query},
            ],
            model=GPT_MODEL,
            temperature=TEMPERATURE,
        )
        return response.choices[0]["message"]["content"]

    @retry(
        wait=wait_random_exponential(min=0.2, max=60),
        stop=stop_after_attempt(6),
        after=lambda retry_state: handle_after_retry(retry_state),
    )
    def query_stream(self, query: str, system_prompt: str = GENERAL_SYSTEM_PROMPT):
        api_response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": query},
            ],
            model=GPT_MODEL,
            temperature=TEMPERATURE,
            stream=True,
        )

        for chunk in api_response:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                content = delta["content"]
                print(content, end="")

    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def get_embedding(self, text: str):
        try:
            response = self.client.embeddings.create(
                input=[text], model=EMBEDDING_MODEL
            )
        except openai.OpenAIError as e:
            raise RuntimeError(f"OpenAI API error: {e}") from e

        # Defensive checks
        try:
            embedding = response.data[0].embedding
            return np.asarray(embedding, dtype=np.float32)
        except (AttributeError, IndexError) as e:
            print("❌ Malformed OpenAI response:", response)
            raise ValueError("Invalid OpenAI response: missing 'embedding'") from e


GPT_3_MODELS = {4096: "gpt-3.5-turbo", 16384: "gpt-3.5-turbo-16k"}
GPT_4_MODELS = {8192: "gpt-4", 32768: "gpt-4-32k"}
