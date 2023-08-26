from pathlib import Path
from typing import List

from ..file_handler.abstract_handler import VSCodeExtCodeLensCode
from .abstract_extractor import AbstractCodeExtractor


class CodeVscodeFileExtractor(AbstractCodeExtractor):
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def extract_functions_from_file(self) -> List[VSCodeExtCodeLensCode]:
        handler = self.get_handler(self.file_path)
        code_blocks = []
        if handler:
            code_blocks = handler().extract_vscode_ext_codelens(self.file_path)
        return code_blocks
