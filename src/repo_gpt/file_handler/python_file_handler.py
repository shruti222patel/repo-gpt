from pathlib import Path
from typing import List

from redbaron import RedBaron

from .abstract_handler import AbstractHandler, ParsedCode


class PythonFileHandler(AbstractHandler):
    def get_function_name(self, code):
        assert code.startswith("def ")
        return code[len("def ") : code.index("(")]

    def get_class_name(self, code):
        assert code.startswith("def ")
        return code[len("class ") : code.index(":")]

    def extract_code(self, filepath: Path) -> List[ParsedCode]:
        with open(filepath, "r", encoding="utf-8") as source_code:
            try:
                code = RedBaron(source_code.read())
                return self.parse_tree(code, filepath)
            except Exception as e:
                print(f"Failed to parse file {filepath}: {e}")
                raise

    def parse_tree(self, tree, filepath: str) -> List[ParsedCode]:
        parsed_nodes = []
        # Loop through all functions and classes in the Python file
        for node in tree.find_all(("def", "class"), recursive=True):
            node_fst = node.fst()
            name = node_fst.get("name")
            if node.type == "def":
                parsed_nodes.append(self.get_function_parsed_code(node))
            elif node.type == "class":
                parsed_nodes.append(self.get_class_and_method_parsed_code(node))
        return parsed_nodes

    def get_function_parsed_code(self, function_node) -> ParsedCode:
        node_fst = function_node.fst()
        name = node_fst.get("name")
        return ParsedCode(
            name=name,
            code_type="function",
            code=function_node.dumps(),
        )

    def get_class_and_method_parsed_code(self, class_node) -> ParsedCode:
        node_fst = class_node.fst()
        name = node_fst.get("name")
        return ParsedCode(
            name=name,
            code_type="class",
            code=self.summarize_class(class_node),
        )

    def summarize_class(self, class_node) -> str:
        summaries = []

        class_summary = [f"class {class_node.name}:"]

        # Summarize class methods
        function_nodes = class_node.find_all("def")
        for function_node in function_nodes:
            # Get the function's parameters as a string
            parameters = ", ".join([param.dumps() for param in function_node.arguments])

            # Get the function's docstring, if it exists
            docstring = ""
            if function_node.value and function_node.value[0].type == "string":
                docstring = function_node.value[0].value

            class_summary.append(
                f"    def {function_node.name}({parameters}):\n        {docstring}\n        ..."
            )

        summaries.append("\n".join(class_summary))

        return "\n".join(summaries)
