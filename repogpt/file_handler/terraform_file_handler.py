from pathlib import Path
from typing import List, Union

from tree_sitter_languages.core import get_language, get_parser

from repogpt.file_handler.abstract_handler import (
    AbstractHandler,
    CodeType,
    ParsedCode,
    VSCodeExtCodeLensCode,
)


class TerraformModuleExtractor(AbstractHandler):
    def __init__(self):
        lang = "hcl"
        self.language = get_language(lang)
        self.parser = get_parser(lang)

    def extract_code(self, filepath: Union[Path, str]) -> List[ParsedCode]:
        with open(filepath, "r", encoding="utf-8") as file:
            source_code = file.read()
            tree = self.parser.parse(bytes(source_code, "utf8"))
            return self._parse_tree(tree, str(filepath))

    def _parse_tree(self, tree, filepath: str) -> List[ParsedCode]:
        parsed_codes = []
        query = self.language.query(
            """
[
  (block)
] @fold
        """
        )

        captures = query.captures(tree.root_node)
        for fold, _ in captures:
            name = None
            code_type = None
            for child in fold.children:
                if child.type == "identifier":
                    code_type = CodeType.__members__.get(
                        child.text.decode("utf8").strip().upper()
                    )
                elif child.type == "string_literal":
                    name = (
                        child.text.decode("utf8")
                        .replace('"', "")
                        .replace("'", "")
                        .strip()
                    )
            parsed_codes.append(
                ParsedCode(
                    function_name=name,
                    class_name=None,
                    code_type=code_type,
                    code=fold.text.decode("utf8").strip(),
                    summary=None,
                    inputs=None,
                    outputs=None,
                )
            )

        return parsed_codes

    def is_valid_code(self, code: str) -> bool:
        try:
            tree = self.parser.parse(bytes(code, "utf8"))
            return tree.root_node.has_error()
        except:
            return False

    def extract_vscode_ext_codelens(
        self, filepath: Path
    ) -> List[VSCodeExtCodeLensCode]:
        # Implement a method to extract VSCode extension codelens information from the file
        pass
