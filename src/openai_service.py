# Set your OpenAI API key as an environment variable
import os
import time
from typing import Any, Callable

import openai as openai
from tenacity import (  # for exponential backoff
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

openai.api_key = os.environ["OPENAI_API_KEY"]
MAX_RETRIES = 3

GPT_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"


class OpenAIService:
    # @retry(wait=wait_random_exponential(min=0.2, max=60), stop=stop_after_attempt(6))
    def get_answer(self, query: str, code: str):
        query = f"""Use the code below to answer the subsequent question. If the answer cannot be found, write "I don't know."
        ```
        {code}
        ```
        Question: {query}"""

        response = openai.ChatCompletion.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful world-class Python developer and technical writer specializing in understanding code and explaining it clearly. You answer questions about codebases.",
                },
                {"role": "user", "content": query},
            ],
            model=GPT_MODEL,
            temperature=0,
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

        return response["data"][0]["embedding"]
