import ast
from pathlib import Path
from typing import List

from file_handler.abstract_handler import AbstractHandler, ParsedCode
from file_handler.handler_registry import register_handler


@register_handler(".py")
class PythonFileHandler(AbstractHandler):
    @staticmethod
    def get_function_name(code):
        assert code.startswith("def ")
        return code[len("def ") : code.index("(")]

    @staticmethod
    def get_until_no_space(all_lines, i) -> str:
        ret = [all_lines[i]]
        for j in range(i + 1, i + 10000):
            if j < len(all_lines):
                if len(all_lines[j]) == 0 or all_lines[j][0] in [" ", "\t", ")"]:
                    ret.append(all_lines[j])
                else:
                    break
        return "\n".join(ret)

    def extract_code(self, filepath: Path) -> List[ParsedCode]:
        with open(filepath, "r") as source_code:
            try:
                tree = ast.parse(source_code.read())
                return self.parse_tree(tree)
            except Exception as e:
                print(f"Failed to parse file {filepath}: {e}")

    def parse_tree(self, tree):
        if ast.iter_child_nodes(tree) is None:
            return []
        parsed_nodes = []
        for node in ast.iter_child_nodes(tree):
            parsed_node_segment = self.parse_tree(node)
            if isinstance(node, ast.FunctionDef):
                parsed_node_segment.append(
                    ParsedCode(
                        name=node.name, code_type="function", code=ast.unparse(node)
                    )
                )
            elif isinstance(node, ast.ClassDef):
                parsed_node_segment.append(
                    ParsedCode(
                        name=node.name, code_type="class", code=ast.unparse(node)
                    )
                )
            parsed_nodes.extend(parsed_node_segment)
        return parsed_nodes
