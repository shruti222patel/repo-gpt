from typing import List

from ..file_handler.abstract_handler import VSCodeExtCodeLensCode
from .abstract_extractor import (
    AbstractCodeExtractor,
    get_language_handler_from_language_name,
)


class CodeVscodeFileExtractor(AbstractCodeExtractor):
    def extract_functions_from_file(
        self, file_path: str
    ) -> List[VSCodeExtCodeLensCode]:
        handler = AbstractCodeExtractor.get_handler(file_path)
        code_blocks = []
        if handler:
            with open(file_path, "r", encoding="utf-8") as source_code:
                code = source_code.read()
                code_blocks = handler().extract_vscode_ext_codelens(code)
        return code_blocks

    def extract_functions_from_file_data(
        self, file_data: str, language: str
    ) -> List[VSCodeExtCodeLensCode]:
        handler = get_language_handler_from_language_name(language)
        code_blocks = []
        if handler:
            code_blocks = handler.extract_vscode_ext_codelens(file_data)
        return code_blocks
