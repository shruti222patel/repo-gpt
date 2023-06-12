from typing import List

import openai
import pandas as pd

from file_handler.abstract_handler import CodeBlock
from openai_service import get_embedding


class CodeProcessor:
    def __init__(self, code_root):
        # Todo: add code root
        self.code_root = code_root

    def process(self, code_blocks: List[CodeBlock]):
        df = pd.DataFrame(code_blocks)
        df["code_embedding"] = df["code"].apply(get_embedding)

        return df
