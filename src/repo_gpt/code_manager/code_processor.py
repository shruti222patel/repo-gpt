from typing import List

import pandas as pd
from tqdm import tqdm

from ..console import verbose_print
from ..file_handler.abstract_handler import ParsedCode
from ..openai_service import OpenAIService

tqdm.pandas()


class CodeProcessor:
    def __init__(self, code_root, openai_service: OpenAIService = None):
        # Todo: add code root
        self.code_root = code_root
        self.openai_service = openai_service if openai_service else OpenAIService()

    def process(self, code_blocks: List[ParsedCode]):
        if len(code_blocks) == 0:
            verbose_print("No code blocks to process")
            return None
        df = pd.DataFrame(code_blocks)
        verbose_print(
            f"Generating openai embeddings for {len(df)} code blocks. This may take a while because of rate limiting..."
        )

        err_cnt = 0

        def safe_get_embedding(code):
            try:
                return self.openai_service.get_embedding(code)
            except Exception as e:
                print(f"Error generating embedding for code: {code}. Error: {e}")
                return None

        df["code_embedding"] = df["code"].progress_apply(safe_get_embedding)
        return df
