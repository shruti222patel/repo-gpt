from pathlib import Path
from typing import List, Union

from tree_sitter_languages import get_language, get_parser

from .abstract_handler import (
    AbstractHandler,
    CodeType,
    ParsedCode,
    VSCodeExtCodeLensCode,
)


class GenericSQLFileHandler(AbstractHandler):
    def __init__(self):
        lang = "sql"
        self.language = get_language(lang)
        self.parser = get_parser(lang)

        self.select_node_type = "select_statement"
        self.update_node_type = "update_statement"
        self.delete_node_type = "delete_statement"
        self.insert_node_type = "insert_statement"
        self.function_definition_node_type = "create_function_statement"
        # There isn't a node type for CTEs

    """VSCode Extension CodeLens"""

    def extract_vscode_ext_codelens(
        self, filepath: Path
    ) -> List[VSCodeExtCodeLensCode]:
        with open(filepath, "r", encoding="utf-8") as source_code:
            code = source_code.read()
            tree = self.parser.parse(bytes(code, "utf8"))
            return self._parse_vscode_ext_codelens(tree)

    def _parse_vscode_ext_codelens(self, tree) -> List[VSCodeExtCodeLensCode]:
        parsed_nodes = []
        root_node = tree.root_node
        for node in root_node.children:
            code_type = self._get_node_code_type(node)
            if code_type is not None:
                parsed_nodes.append(
                    VSCodeExtCodeLensCode(
                        name=code_type.value,
                        start_line=node.start_point[0],
                        end_line=node.end_point[0],
                    )
                )
        return parsed_nodes

    def _get_node_code_type(self, node):
        code_type = None
        if node.type == self.select_node_type:
            code_type = CodeType.SELECT
        elif node.type == self.update_node_type:
            code_type = CodeType.UPDATE
        elif node.type == self.delete_node_type:
            code_type = CodeType.DELETE
        elif node.type == self.insert_node_type:
            code_type = CodeType.INSERT
        elif node.type == self.function_definition_node_type:
            code_type = CodeType.FUNCTION
        return code_type

    """Repo GPT"""

    def extract_code(self, filepath: Union[Path, str]) -> List[ParsedCode]:
        with open(filepath, "r", encoding="utf-8") as source_code:
            code = source_code.read()
            tree = self.parser.parse(bytes(code, "utf8"))
            return self._parse_tree(tree)

    def _parse_tree(self, tree) -> List[ParsedCode]:
        parsed_nodes = []
        root_node = tree.root_node
        for node in root_node.children:
            code_type = self._get_node_code_type(node)
            if code_type is not None:
                parsed_nodes.append(
                    ParsedCode(
                        function_name=None,
                        class_name=None,
                        code_type=code_type,
                        code=node.text.decode("utf8"),
                        inputs=None,
                        summary=None,
                        outputs=None,
                    )
                )
        return parsed_nodes

    def is_valid_code(self, code: str) -> bool:
        tree = self.parser.parse(bytes(code, "utf8"))
        errors = (
            tree.root_node.children[-1].type == "ERROR"
            if tree.root_node.children
            else False
        )
        return not errors
