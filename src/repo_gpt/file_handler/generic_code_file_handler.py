from pathlib import Path
from typing import List, Tuple

from tree_sitter_languages import get_language, get_parser

from .abstract_handler import AbstractHandler, CodeType, ParsedCode


class GenericCodeFileHandler(AbstractHandler):
    def __init__(
        self,
        lang: str,
        function_name_node_type: str,
        class_name_node_type: str,
        function_node_type: str,
        class_node_type: str,
        method_node_type: str,
        class_internal_node_type: str,
        parent_class_node_type: str,
        function_output_node_type: str = "output",
        function_parameters_node_type: str = "parameters",
    ):
        self.function_name_node_type = function_name_node_type
        self.class_name_node_type = class_name_node_type
        self.function_node_type = function_node_type
        self.class_node_type = class_node_type
        self.method_node_type = method_node_type
        self.class_internal_node_type = class_internal_node_type
        self.parent_class_node_type = parent_class_node_type
        self.function_output_node_type = function_output_node_type
        self.function_parameters_node_type = function_parameters_node_type

        self.language = get_language(lang)
        self.parser = get_parser(lang)
        self.parser.set_language(self.language)

    def get_function_name(self, function_node):
        for node in function_node.named_children:
            if node.type == self.function_name_node_type:
                return node.text.decode("utf8")

    def get_class_name(self, class_node):
        for node in class_node.named_children:
            if node.type == self.class_name_node_type:
                return node.text.decode("utf8")

    def extract_code(self, filepath: Path) -> List[ParsedCode]:
        with open(filepath, "r", encoding="utf-8") as source_code:
            try:
                code = source_code.read()
                tree = self.parser.parse(bytes(code, "utf8"))
                return self.parse_tree(tree, filepath)
            except Exception as e:
                print(f"Failed to parse file {filepath}: {e}")
                raise

    def parse_tree(self, tree, filepath: str) -> List[ParsedCode]:
        parsed_nodes = []
        root_node = tree.root_node
        for node in root_node.children:
            if node.type == self.function_node_type:
                parsed_nodes.append(self.get_function_parsed_code(node))
            elif node.type == self.class_node_type:
                parsed_nodes.extend(self.get_class_and_method_parsed_code(node))
        return parsed_nodes

    def get_function_parsed_code(self, function_node, is_method=False) -> ParsedCode:
        name = self.get_function_name(function_node)
        input_params, output_params = self.get_function_parameters(function_node)
        return ParsedCode(
            name=name,
            code_type=CodeType.METHOD if is_method else CodeType.FUNCTION,
            code=function_node.text.decode("utf8"),
            summary=None,
            inputs=input_params,
            outputs=output_params,
        )

    def get_class_and_method_parsed_code(self, class_node) -> List[ParsedCode]:
        parsed_codes = []
        class_name = self.get_class_name(class_node)
        parent_classes = self.get_parent_classes(class_node)
        class_summary = [f"class: {class_name}\n    parent classes: {parent_classes}\n"]
        for node in class_node.named_children:
            if node.type == self.class_internal_node_type:
                for n in node.named_children:
                    if n.type == self.method_node_type:
                        # function
                        parsed_code = self.get_function_parsed_code(n, is_method=True)
                        # TODO figure out how to get docstring
                        parsed_codes.append(parsed_code)
                        input_params, output_params = self.get_function_parameters(n)
                        class_summary.append(
                            f"    method: {parsed_code.name}\n        input parameters: {input_params}\n        output parameters: {output_params}\n        code: ...\n"
                        )

        name = self.get_class_name(class_node)
        parsed_codes.append(
            ParsedCode(
                name=name,
                code_type=CodeType.CLASS,
                code=class_node.text.decode("utf8"),
                summary="\n".join(class_summary),
                inputs=parent_classes,
                outputs=None,
            )
        )

        return parsed_codes

    def get_parent_classes(self, class_node) -> Tuple[str, ...]:
        for child in class_node.children:
            # If we found the base_classes node
            if child.type == self.parent_class_node_type:
                return tuple(
                    grandchild.text.decode("utf8")
                    for grandchild in child.named_children
                    if grandchild.type == self.class_name_node_type
                )
        return None

    def get_function_parameters(
        self, function_node
    ) -> (Tuple[str, ...], Tuple[str, ...]):
        input_params, output_params = None, None
        for child in function_node.children:
            # If we found the parameters node
            if child.type in self.function_parameters_node_type:
                input_params = tuple(
                    grandchild.text.decode("utf8")
                    for grandchild in child.named_children
                    # if grandchild.type == self.function_name_node_type
                )
            if child.type == self.function_output_node_type:
                output_params = tuple(
                    grandchild.text.decode("utf8")
                    for grandchild in child.named_children
                )
        return (
            input_params if input_params and len(input_params) > 0 else None,
            output_params if output_params and len(output_params) > 0 else None,
        )


class PHPFileHandler(GenericCodeFileHandler):
    def __init__(self):
        super().__init__(
            lang="php",
            function_name_node_type="name",
            class_name_node_type="name",
            function_node_type="function_definition",
            class_node_type="class_declaration",
            method_node_type="method_declaration",
            class_internal_node_type="declaration_list",
            parent_class_node_type="base_clause",
            function_output_node_type="union_type",
            function_parameters_node_type="function_parameters_node_type",
        )


class PythonFileHandler(GenericCodeFileHandler):
    def __init__(self):
        super().__init__(
            lang="python",
            function_name_node_type="identifier",
            class_name_node_type="identifier",
            function_node_type="function_definition",
            class_node_type="class_definition",
            method_node_type="function_definition",
            class_internal_node_type="block",
            parent_class_node_type="argument_list",
            function_output_node_type="type",
        )
