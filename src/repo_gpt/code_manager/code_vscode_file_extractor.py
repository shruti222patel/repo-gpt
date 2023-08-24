from pathlib import Path
from typing import List

from ..file_handler.abstract_handler import ParsedCode
from .abstract_extractor import AbstractCodeExtractor


class CodeDirExtractor(AbstractCodeExtractor):
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def extract_functions_from_file(self) -> List[ParsedCode]:
        handler = self.get_handler(self.file_path)
        code_blocks = []
        if handler:
            code_blocks = handler().extract(self.file_path)
        return code_blocks
