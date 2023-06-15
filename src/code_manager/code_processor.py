from typing import List

import pandas as pd
from tqdm import tqdm

from file_handler.abstract_handler import CodeBlock
from openai_service import OpenAIService

tqdm.pandas()


class CodeProcessor:
    def __init__(self, code_root):
        # Todo: add code root
        self.code_root = code_root
        self.openai_service = OpenAIService()

    def process(self, code_blocks: List[CodeBlock]):
        if len(code_blocks) == 0:
            print("No code blocks to process")
            return None
        df = pd.DataFrame(code_blocks)
        print(
            f"Generating openai embeddings for {len(df)} code blocks. This may take a while because of rate limiting..."
        )
        df["code_embedding"] = df["code"].progress_apply(
            self.openai_service.get_embedding
        )
        return df
