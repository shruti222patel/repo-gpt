import asyncio
import logging
from itertools import islice
from typing import List, Optional

import numpy as np
import pandas as pd
import tiktoken
from tqdm import tqdm

from ..console import verbose_print
from ..file_handler.abstract_handler import ParsedCode
from ..openai_service import OpenAIService, tokens_from_string

logger = logging.getLogger(__name__)


class CodeProcessor:
    ENCODING = tiktoken.get_encoding("cl100k_base")

    def __init__(
        self,
        code_root,
        openai_service: OpenAIService = None,
        max_concurrent_embedding_requests=1000,
    ):
        # Todo: add code root
        self.code_root = code_root
        self.openai_service = openai_service if openai_service else OpenAIService()
        self.semaphore = asyncio.Semaphore(
            max_concurrent_embedding_requests
        )  # Control concurrency

    async def process(self, code_blocks: List[ParsedCode]) -> Optional[pd.DataFrame]:
        if len(code_blocks) == 0:
            return None

        df = pd.DataFrame(code_blocks)

        async def len_safe_get_embedding(text):
            max_tokens = 8191

            chunk_embeddings = []
            chunk_lens = []

            async with self.semaphore:  # Semaphore will limit the number of concurrent get_embedding calls
                for chunk in CodeProcessor._chunked_tokens(
                    text, chunk_length=max_tokens
                ):
                    embedding = await self.openai_service.get_embedding_async(chunk)
                    chunk_embeddings.append(embedding)
                    chunk_lens.append(len(chunk))

            chunk_embedding = np.average(chunk_embeddings, axis=0, weights=chunk_lens)
            normalized_embedding = chunk_embedding / np.linalg.norm(chunk_embedding)
            return normalized_embedding

        # Generate embeddings concurrently for all code blocks, limited by the semaphore
        tasks = [len_safe_get_embedding(code) for code in df["code"]]
        embeddings = await asyncio.gather(*tasks)
        df["code_embedding"] = embeddings

        return df

    @staticmethod
    def _batched(iterable, n):
        """Batch data into lists of length n. The last batch may be shorter."""
        if n < 1:
            raise ValueError("n must be at least one")
        it = iter(iterable)
        return iter(lambda: list(islice(it, n)), [])

    @staticmethod
    def _chunked_tokens(text, chunk_length):
        tokens = CodeProcessor.ENCODING.encode(text)
        chunks_iterator = CodeProcessor._batched(tokens, chunk_length)
        yield from chunks_iterator
