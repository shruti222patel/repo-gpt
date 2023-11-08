from collections import deque
from pathlib import Path
from typing import Any, List, Optional, Tuple

from tree_sitter_languages import get_language, get_parser

from .abstract_handler import (
    AbstractHandler,
    CodeType,
    ParsedCode,
    VSCodeExtCodeLensCode,
)


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
        parent_class_name_node_type: str,
        method_name_node_type: str,
        function_output_node_type: str = "output",
        function_parameters_node_type: str = "parameters",
        root_node_type: str = "source_file",
        function_query: Optional[str] = None,
        class_query: Optional[str] = None,
        method_query: Optional[str] = None,
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
        self.parent_class_name_node_type = parent_class_name_node_type
        self.method_name_node_type = method_name_node_type
        self.root_node_type = root_node_type

        self.language = get_language(lang)
        self.parser = get_parser(lang)
        self.parser.set_language(self.language)

        self.function_query = (
            function_query
            if function_query
            else f"""
                   ({self.function_node_type}) @function
                   """
        )
        self.class_query = (
            class_query
            if class_query
            else f"""
                   ({class_node_type}) @class
                   """
        )
        self.method_query = (
            method_query
            if method_query
            else f"""
                   ({self.method_node_type}) @method
                   """
        )

    def summarize_file(self, filepath: Path) -> str:
        # Use the `extract_code` method to parse the given file and get all code structures.
        parsed_codes = self.extract_code(filepath)

        summaries = []

        for parsed_code in parsed_codes:
            if parsed_code.code_type == CodeType.CLASS:
                class_summary = f"Class: {parsed_code.class_name}"
                if parsed_code.inputs:
                    class_summary += (
                        f"\n\tParent Classes: {', '.join(parsed_code.inputs)}"
                    )
                summaries.append(class_summary)

                # Including the methods and their IO signatures within the class
                for line in parsed_code.summary.split("\n"):
                    if line.strip().startswith("method:"):
                        summaries.append("\t" + line.strip())

            elif parsed_code.code_type == CodeType.FUNCTION:
                function_summary = f"Function: {parsed_code.function_name}"
                if parsed_code.inputs:
                    function_summary += (
                        f"\n\tInput Parameters: {', '.join(parsed_code.inputs)}"
                    )
                if parsed_code.outputs:
                    function_summary += (
                        f"\n\tOutput Parameters: {', '.join(parsed_code.outputs)}"
                    )
                summaries.append(function_summary)

            elif parsed_code.code_type == CodeType.METHOD:
                # This section might not be necessary as methods are captured under the class summary.
                method_summary = f"Method (within class): {parsed_code.function_name}"
                if parsed_code.inputs:
                    method_summary += (
                        f"\n\tInput Parameters: {', '.join(parsed_code.inputs)}"
                    )
                if parsed_code.outputs:
                    method_summary += (
                        f"\n\tOutput Parameters: {', '.join(parsed_code.outputs)}"
                    )
                summaries.append(method_summary)

        return "\n".join(summaries)

    """ VSCode Extension CodeLens """

    def extract_vscode_ext_codelens(
        self, filepath: Path
    ) -> List[VSCodeExtCodeLensCode]:
        with open(filepath, "r", encoding="utf-8") as source_code:
            code = source_code.read()
            tree = self.parser.parse(bytes(code, "utf8"))
            return self.parse_vscode_ext_codelens(tree)

    def _query(self, query: str, root_node) -> List[Tuple[str, int, int]]:
        query = self.language.query(query)
        return query.captures(root_node)

    def parse_vscode_ext_codelens(self, tree) -> List[VSCodeExtCodeLensCode]:
        return self.parse_code(
            tree,
            self.get_vscode_class_code,
            self.get_vscode_function_code,
            self.get_vscode_function_code,
        )

    def parse_code(
        self,
        tree,
        class_parsing_func,
        function_parsing_func,
        method_parsing_func,
        global_parsing_func=None,
    ) -> List[Any]:
        parsed_nodes = []
        root_node = tree.root_node

        # Get all classes
        class_matches = self._get_all_classes(root_node)
        for match in class_matches:
            parsed_nodes.append(class_parsing_func(match[0]))

        # Get all functions
        function_matches = self._get_all_functions(root_node)
        for match in function_matches:
            parsed_nodes.append(function_parsing_func(match[0]))

        # Get all methods
        method_matches = []
        if self.method_node_type != self.function_node_type:
            method_matches = self._get_all_methods(root_node)
            for match in method_matches:
                parsed_nodes.append(method_parsing_func(match[0]))

        if global_parsing_func != None:
            parsed_node = self._get_all_global_code(
                root_node, class_matches + function_matches + method_matches
            )
            if parsed_node != None:
                parsed_nodes.append(parsed_node)

        return parsed_nodes

    def _get_all_classes(self, node):
        return self._query(self.class_query, node)

    def _get_all_functions(self, node):
        return self._query(self.function_query, node)

    def _get_all_methods(self, node):
        return self._query(self.method_query, node)

    def _get_all_global_code(self, node, nodes_to_remove=None):
        source_code = node.text.decode("utf8")
        # Convert source code to a list of lines
        lines = source_code.split("\n")

        # Mark lines that belong to functions for removal
        for node, _ in nodes_to_remove:
            for line_num in range(node.start_point[0] - 1, node.end_point[0]):
                lines[line_num] = None

        # Remove the marked lines
        remaining_lines = [
            line for line in lines if line is not None and line.strip() != ""
        ]
        if len(remaining_lines) == 0:
            return None
        modified_source_code = "\n".join(line for line in lines if line is not None)

        return ParsedCode(
            function_name=None,
            class_name=None,
            code_type=CodeType.GLOBAL,
            code=modified_source_code,
            summary=None,
            inputs=None,
            outputs=None,
        )

    def get_vscode_function_code(self, function_node) -> VSCodeExtCodeLensCode:
        name = self.get_function_name(function_node)
        return VSCodeExtCodeLensCode(
            name=name,
            start_line=function_node.start_point[0],
            end_line=function_node.end_point[0],
            # code=function_node.text.decode("utf8"),
        )

    def get_vscode_class_code(self, class_node) -> List[VSCodeExtCodeLensCode]:
        class_name = self.get_class_name(class_node)
        return VSCodeExtCodeLensCode(
            name=class_name,
            start_line=class_node.start_point[0],
            # code=class_node.text.decode("utf8"),
            end_line=class_node.end_point[0],
        )

    """ General Repo GPT """

    def get_function_name(self, function_node):
        for node in function_node.named_children:
            if (
                node.type == self.function_name_node_type
                or node.type == self.method_name_node_type
            ):
                return node.text.decode("utf8")

    def get_class_name(self, class_node):
        for node in class_node.named_children:
            if node.type == self.class_name_node_type:
                return node.text.decode("utf8")

    def extract_code(self, filepath: Path) -> List[ParsedCode]:
        with open(filepath, "r", encoding="utf-8") as source_code:
            code = source_code.read()
            tree = self.parser.parse(bytes(code, "utf8"))
            return self.parse_tree(tree)

    def parse_tree(self, tree) -> List[ParsedCode]:
        parsed_codes = self.parse_code(
            tree,
            self.get_class_parsed_code,
            self.get_function_parsed_code,
            self.get_function_parsed_code,
            self._get_all_global_code,
        )
        return parsed_codes

    def get_function_parsed_code(
        self, function_node, class_name=None, is_method=False
    ) -> ParsedCode:
        name = self.get_function_name(function_node)
        input_params, output_params = self.get_function_parameters(function_node)
        return ParsedCode(
            function_name=name,
            class_name=class_name,
            code_type=CodeType.METHOD if is_method else CodeType.FUNCTION,
            code=function_node.text.decode("utf8"),
            summary=None,
            inputs=input_params,
            outputs=output_params,
        )

    def get_class_parsed_code(self, class_node) -> ParsedCode:
        class_name = self.get_class_name(class_node)
        parent_classes = self.get_parent_classes(class_node)
        class_summary = [f"class: {class_name}\n    parent classes: {parent_classes}\n"]
        for node in class_node.named_children:
            if node.type == self.class_internal_node_type:
                # TODO get method nodes by query instea
                for n in node.named_children:
                    if n.type == self.method_node_type:
                        # function
                        parsed_code = self.get_function_parsed_code(
                            n, class_name=class_name, is_method=True
                        )
                        input_params, output_params = self.get_function_parameters(n)
                        class_summary.append(
                            f"    method: {parsed_code.function_name}\n        input parameters: {input_params}\n        output parameters: {output_params}\n        code: ...\n"
                        )

        return ParsedCode(
            function_name=None,
            class_name=class_name,
            code_type=CodeType.CLASS,
            code=class_node.text.decode("utf8"),
            summary="\n".join(class_summary),
            inputs=parent_classes,
            outputs=None,
        )

    def get_parent_classes(self, class_node) -> Tuple[str, ...]:
        for child in class_node.children:
            # If we found the base_classes node
            if child.type == self.parent_class_node_type:
                queue = deque(child.named_children)
                while len(queue):
                    node = queue.popleft()
                    if node.type == self.parent_class_name_node_type:
                        return (
                            tuple(
                                grandchild.text.decode("utf8")
                                for grandchild in node.named_children
                            )
                            if len(node.named_children) > 0
                            else (node.text.decode("utf8"),)
                        )
                    else:
                        queue.extend(node.named_children)
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

    def is_valid_code(self, code: str) -> bool:
        tree = self.parser.parse(bytes(code, "utf8"))
        errors = (
            tree.root_node.children[-1].type == "ERROR"
            if tree.root_node.children
            else False
        )
        return not errors


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
            parent_class_name_node_type="name",
            method_name_node_type="name",
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
            parent_class_name_node_type="identifier",
            method_name_node_type="identifier",
        )


class TypeScriptFileHandler(GenericCodeFileHandler):
    def __init__(self):
        super().__init__(
            lang="typescript",
            function_name_node_type="identifier",
            class_name_node_type="type_identifier",
            parent_class_name_node_type="identifier",
            function_node_type="function_declaration",
            class_node_type="class_declaration",
            method_node_type="method_definition",
            class_internal_node_type="class_body",
            parent_class_node_type="class_heritage",
            function_output_node_type="type_annotation",
            function_parameters_node_type="formal_parameters",
            method_name_node_type="property_identifier",
            root_node_type="program",
        )


class ElixirFileHandler(GenericCodeFileHandler):
    def __init__(self):
        super().__init__(
            lang="elixir",
            function_name_node_type="identifier",  # Placeholder, might differ
            class_name_node_type="identifier",  # Elixir has modules, not classes
            function_node_type=None,
            class_node_type=None,  # Elixir has modules, not classes
            method_node_type=None,
            class_internal_node_type="module_body",
            parent_class_node_type="use_clause",  # Elixir uses `use` for certain extensions
            function_output_node_type="type_annotation",  # Placeholder, Elixir's type annotations are different
            function_parameters_node_type="function_parameters",
            parent_class_name_node_type="module_name",  # Elixir has modules, not classes
            method_name_node_type="function_name",
            root_node_type="program",
            function_query="""
(call
  target: (identifier) @ignore
  (arguments
    [
      ; regular function clause
      (call target: (identifier) @name)
      ; function clause with a guard clause
      (binary_operator
        left: (call target: (identifier) @name)
        operator: "when")
    ])
  (#match? @ignore "^(def|defp|defdelegate|defguard|defguardp|defmacro|defmacrop|defn|defnp)$")) @function
""",
            class_query="""
(call
  target: (identifier) @ignore
  (arguments (alias) @name)
  (#match? @ignore "^(defmodule|defprotocol)$")) @definition.module
""",
        )


"""Code File Handler"""


class GenericCodeFileHandler:
    pass
