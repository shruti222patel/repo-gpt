# Set your OpenAI API key as an environment variable
import os
import time
from typing import Any, Callable

import numpy as np
import openai as openai
import tiktoken
from tenacity import (  # for exponential backoff
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

openai.api_key = os.environ["OPENAI_API_KEY"]

MAX_RETRIES = 3
GPT_MODEL = "gpt-3.5-turbo"  # "gpt-3.5-turbo-16k"
EMBEDDING_MODEL = "text-embedding-ada-002"
TEMPERATURE = (
    0.4  # temperature = 0 can sometimes get stuck in repetitive loops, so we use 0.4
)


def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
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
        print(
            "Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613."
        )
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        print(
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
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


class OpenAIService:
    GENERAL_SYSTEM_PROMPT = "You are a world-class software engineer and technical writer specializing in understanding code + architecture + tradeoffs and explaining them clearly and in detail. You are helpful and answer questions the user asks. You organize your explanations in markdown-formatted, bulleted lists."
    ANALYSIS_SYSTEM_PROMPT = "You are a world-class Python developer with an eagle eye for unintended bugs and edge cases. You carefully explain code with great detail and accuracy. You organize your explanations in markdown-formatted, bulleted lists."

    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def get_answer(
        self, query: str, code: str, system_prompt: str = GENERAL_SYSTEM_PROMPT
    ):
        query = f"""Use the code below to answer the subsequent question. If the answer cannot be found, write "I don't know."
        ```
        {code}
        ```
        Question: {query}"""

        response = openai.ChatCompletion.create(
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

    def _retry_on_exception(self, func: Callable[..., Any], *args, **kwargs):
        for retry in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception:
                if retry < MAX_RETRIES - 1:  # if it's not the last retry
                    sleep_time = 2**retry  # exponential backoff
                    time.sleep(sleep_time)
                else:  # if it's the last retry, re-raise the exception
                    raise

    @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def get_embedding(self, text: str):
        response = openai.Embedding.create(input=[text], model=EMBEDDING_MODEL)

        if (
            "data" not in response
            or len(response["data"]) == 0
            or "embedding" not in response["data"][0]
        ):
            raise ValueError(
                "Invalid response from OpenAI API: 'data' field missing or empty, or 'embedding' field missing"
            )

        return np.asarray(response["data"][0]["embedding"], dtype=np.float32)


GPT_3_MODELS = {4096: "gpt-3.5-turbo", 16384: "gpt-3.5-turbo-16k"}
GPT_4_MODELS = {8192: "gpt-4", 32768: "gpt-4-32k"}
