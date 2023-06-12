# Set your OpenAI API key as an environment variable
import os

import openai as openai

openai.api_key = os.environ["OPENAI_API_KEY"]
MAX_RETRIES = 3


def get_embedding(text: str):
    """
    Get the embedding of a document using OpenAI's text embedding model.

    Parameters:
    text (str): Str of code to embed.
    engine (str): The model to use for the embedding. Default is "text-embedding-ada-002".
    max_retries (int): Maximum number of retries in case of API errors or rate limits. Default is 5.

    Returns:
    list: The embedding of the document as a list of floats.
    """

    engine = "text-embedding-ada-002"
    for retry in range(MAX_RETRIES):
        try:
            response = openai.Embedding.create(input=[text], model=engine)
            break  # success, exit the retry loop
        except Exception as e:
            if retry < MAX_RETRIES - 1:  # if it's not the last retry
                sleep_time = 2**retry  # exponential backoff
                time.sleep(sleep_time)
            else:  # if it's the last retry, re-raise the exception
                raise

    if (
        "data" not in response
        or len(response["data"]) == 0
        or "embedding" not in response["data"][0]
    ):
        raise ValueError(
            "Invalid response from OpenAI API: 'data' field missing or empty, or 'embedding' field missing"
        )

    return response["data"][0]["embedding"]
