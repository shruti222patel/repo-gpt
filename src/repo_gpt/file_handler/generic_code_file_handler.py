from typing import List
from pathlib import Path
from tree_sitter_languages import get_language, get_parser


from .abstract_handler import AbstractHandler, ParsedCode

class GenericCodeFileHandler(AbstractHandler):

    def __init__(self):
        self.language = get_language('php')
        self.parser = get_parser('php')
        self.parser.set_language(self.language)
        # self.parser = tree_sitter.Parser()
        # self.parser.set_language(tree_sitter.Language('path_to_compiled_grammar', 'python'))

    def get_function_name(self, function_node):
        for node in function_node.named_children:
            if node.type == "identifier" or node.type == "name":
                return node.text.decode('utf8')

    def get_class_name(self, class_node):
        for node in class_node.named_children:
            if node.type == "identifier" or node.type == "name":
                return node.text.decode('utf8')

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
            if node.type == "function_definition":
                parsed_nodes.append(self.get_function_parsed_code(node))
            elif node.type == "class_definition" or node.type == "class_declaration":
                parsed_nodes.extend(self.get_class_and_method_parsed_code(node))
        return parsed_nodes

    def get_function_parsed_code(self, function_node) -> ParsedCode:
        name = self.get_function_name(function_node)
        return ParsedCode(
            name=name,
            code_type="function",
            code=function_node.text.decode('utf8'),
        )

    def get_class_and_method_parsed_code(self, class_node) -> List[ParsedCode]:

        parsed_codes = []
        class_name = self.get_class_name(class_node)
        class_summary = [f"class: {class_name}"]
        for node in class_node.named_children:
            if node.type == "block" or node.type == "declaration_list":
                for n in node.named_children:
                    if n.type == "function_definition" or n.type == "method_declaration":
                        # function
                        parsed_code = self.get_function_parsed_code(n)
                        parameters = ""
                        # TODO figure out how to get docstring
                        for _n in n.named_children:
                            if _n.type == 'parameters':
                                parameters = _n.text.decode('utf8')
                        parsed_codes.append(parsed_code)
                        class_summary.append(f"    method: {parsed_code.name}\n    parameters: {parameters}\n    code: ...\n")

        name = self.get_class_name(class_node)
        parsed_codes.append(ParsedCode(
            name=name,
            code_type="class",
            code="\n".join(class_summary)
        ))

        return parsed_codes

