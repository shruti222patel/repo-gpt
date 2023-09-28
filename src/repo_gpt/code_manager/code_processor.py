import logging
from typing import List

import pandas as pd
from tqdm import tqdm

from ..console import verbose_print
from ..file_handler.abstract_handler import ParsedCode
from ..openai_service import OpenAIService, tokens_from_string

logger = logging.getLogger(__name__)


class CodeProcessor:
    def __init__(self, code_root, openai_service: OpenAIService = None):
        # Todo: add code root
        self.code_root = code_root
        self.openai_service = openai_service if openai_service else OpenAIService()

    def process(self, code_blocks: List[ParsedCode]):
        if len(code_blocks) == 0:
            logger.verbose_info("No code blocks to process")
            return None
        df = pd.DataFrame(code_blocks)
        logger.verbose_info(
            f"Generating openai embeddings for {len(df)} code blocks. This may take a while because of rate limiting..."
        )

        err_cnt = 0

        def safe_get_embedding(code):
            # Note: this truncates the code to 8096 tokens, which is the limit for the embedding model we use
            # TODO: figure out a way where we don't lose so much info
            try:
                tokens = tokens_from_string(code)
                token_limit = 8096  # Limit for the embedding model we use ADA TODO: Connect this const with the model name
                if len(tokens) > token_limit:
                    code = "".join(tokens[:token_limit])
                return self.openai_service.get_embedding(code)
            except Exception as e:
                print(f"Error generating embedding for code: {code}. Error: {e}")
                return None

        if logger.getEffectiveLevel() < logging.INFO:
            tqdm.pandas()
            df["code_embedding"] = df["code"].progress_apply(safe_get_embedding)
        else:
            df["code_embedding"] = df["code"].apply(safe_get_embedding)
        return df
