import os

import code2flow
import networkx as nx
import pygraphviz as pgv

from repogpt.codebase_analyzer.graph_analyzer import GraphAnalyzer


class FunctionCallAnalyzer(GraphAnalyzer):
    def __init__(self, directory_path, output_file_path="function_call_graph.dot"):
        super().__init__(directory_path, output_file_path)

    def _generate_and_load_graph(self, output_file_path):
        # Generate the code graph using pydeps
        python_files = []

        # Walk through directory and its subdirectories
        for dirpath, dirnames, filenames in os.walk(self.directory_path):
            for file in filenames:
                if file.endswith(".py"):
                    python_files.append(os.path.join(dirpath, file))

        # Generate the code graph
        code2flow.code2flow(python_files, output_file_path)

        # Load the graph from the dot file
        try:
            with open(output_file_path, "r") as file:
                file_content = file.read()

            agraph = pgv.AGraph(string=file_content)
            self.graph = nx.DiGraph(agraph)

            root_nodes = [
                node for node, degree in self.graph.in_degree() if degree == 0
            ]
            if root_nodes:
                self.graph.remove_node(root_nodes[0])

            label_mapping = {
                node: self._clean_name(self.graph.nodes[node]["label"])
                for node in self.graph.nodes()
            }
            self.graph = nx.relabel_nodes(self.graph, label_mapping)

            for node in self.graph.nodes():
                node_data = self.graph.nodes[node]
                for attribute in ["shape", "style", "fillcolor"]:
                    node_data.pop(attribute, None)
                self._extract_attributes_from_name(node_data)

        except FileNotFoundError:
            raise ValueError(f"File '{output_file_path}' not found.")
        except Exception as e:
            raise ValueError(f"Error loading graph from '{output_file_path}': {str(e)}")

    def _clean_name(self, name):
        parts = name.split(":")
        if len(parts) > 1:
            final_parts = parts[1].split("()")
            return final_parts[0].strip() if len(final_parts) > 1 else parts[1].strip()
        return name.strip()

    def _extract_attributes_from_name(self, node_data):
        name_parts = node_data["name"].split("::")
        file_name = name_parts[0]
        if len(name_parts) > 1:
            class_and_function = name_parts[1].rsplit(".", 1)
            class_name = class_and_function[0] if len(class_and_function) > 1 else None
            function_name = class_and_function[-1]
        else:
            class_name = None
            function_name = file_name
            file_name = None
        node_data["file_name"] = file_name
        if class_name:
            node_data["class_name"] = class_name
        node_data["function_name"] = function_name

    # Not really used
    def generate_class_graph(self):
        return self._generate_graph_by_attribute("class_name")

    # Not really used
    def generate_file_graph(self):
        return self._generate_graph_by_attribute("file_name")


# Example Usage:
# analyzer = FunctionCallGraphAnalyzer("/path/to/your/directory")
# graph = analyzer.graph
