from pathlib import Path
from typing import List

from redbaron import RedBaron

from .abstract_handler import AbstractHandler, CodeType, ParsedCode


class PythonFileHandler(AbstractHandler):
    def extract_code(self, filepath: Path) -> List[ParsedCode]:
        with open(filepath, "r", encoding="utf-8") as source_code:
            try:
                code = RedBaron(source_code.read())
                return self.parse_tree(code)
            except Exception as e:
                print(f"Failed to parse file {filepath}: {e}")
                raise

    def parse_tree(self, tree) -> List[ParsedCode]:
        parsed_nodes = []
        # Loop through all functions and classes in the Python file
        for node in tree.find_all(("def", "class"), recursive=True):
            if node.type == "def":
                parsed_nodes.append(self.get_function_parsed_code(node))
            elif node.type == "class":
                parsed_nodes.append(self.get_class_and_method_parsed_code(node))
        return parsed_nodes

    def get_function_parsed_code(self, function_node) -> ParsedCode:
        return ParsedCode(
            name=function_node.name,
            code_type=CodeType.FUNCTION,
            code=function_node.dumps(),
            inputs=(),  # TODO function_node.arguments.dumps(),
        )

    def get_class_and_method_parsed_code(self, class_node) -> ParsedCode:
        return ParsedCode(
            name=class_node.name,
            code_type=CodeType.CLASS,
            code=self.summarize_class(class_node),
            inputs=(),  # TODO: Get class inputs
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
