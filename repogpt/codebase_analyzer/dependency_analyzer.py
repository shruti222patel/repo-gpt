import os
import subprocess

import networkx as nx
import pygraphviz as pgv

from repogpt.codebase_analyzer.graph_analyzer import GraphAnalyzer


class DependencyAnalyzer(GraphAnalyzer):
    def __init__(self, directory_path: str, output_file_path: str = "pydeps_graph.dot"):
        super().__init__(directory_path, output_file_path)

    def _generate_and_load_graph(self, output_file_path):
        # Generate dot file using pydeps
        cmd = [
            "pydeps",
            "--noshow",
            "--max-bacon=1",
            "-T",
            "dot",
            "-o",
            output_file_path,
            self.directory_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("Error occurred while running pydeps:")
            print(result.stderr)
        else:
            print("Command executed successfully!")
            print(result.stdout)

        # Load the graph from the dot file
        try:
            with open(output_file_path, "r") as file:
                file_content = file.read()

            agraph = pgv.AGraph(string=file_content)
            self.graph = nx.DiGraph(agraph)
            print(f"Dependency DOT file saved to {os.path.abspath(output_file_path)}")
        except Exception as e:
            print(f"An error occurred while loading the graph: {e}")


# Example Usage:
# analyzer = DependencyAnalyzer("/path/to/your/source")
# graph = analyzer.graph
