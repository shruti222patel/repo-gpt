from pathlib import Path
from typing import List

from redbaron import RedBaron

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
        # with open(filename, "r", encoding="utf-8") as file:
        #     code = RedBaron(file.read())
        with open(filepath, "r", encoding="utf-8") as source_code:
            try:
                code = RedBaron(source_code.read())
                return self.parse_tree(code)
            except Exception as e:
                print(f"Failed to parse file {filepath}: {e}")

    def parse_tree(self, tree):
        parsed_nodes = []
        # Loop through all functions and classes in the Python file
        for node in tree.find_all(("def", "class")):
            if node.type == "def":
                parsed_nodes.append(
                    ParsedCode(name=node.name, code_type="function", code=node.dumps())
                )
            elif node.type == "class":
                parsed_nodes.append(
                    ParsedCode(name=node.name, code_type="class", code=node.dumps())
                )
        return parsed_nodes
