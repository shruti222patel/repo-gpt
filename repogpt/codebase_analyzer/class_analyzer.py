import os
import subprocess

import networkx as nx
import pygraphviz as pgv

from repogpt.codebase_analyzer.graph_analyzer import GraphAnalyzer


class ClassAnalyzer(GraphAnalyzer):
    def __init__(
        self, directory_path: str, output_file_path: str = "class_diagram.dot"
    ):
        super().__init__(directory_path, output_file_path)

    def _generate_and_load_graph(self, output_file_path):
        # Ensure pylint is installed
        if not self._is_tool_installed("pyreverse"):
            raise EnvironmentError(
                "pyreverse (from pylint) must be installed to use this class."
            )

        # Generate dot file
        try:
            subprocess.run(
                ["pyreverse", "-o", "dot", "-p", "ProjectName", self.directory_path],
                check=True,
            )

            # Rename the generated dot file to the desired name
            os.rename("classes_ProjectName.dot", output_file_path)
            print(f"Dot file generated: {output_file_path}")
        except subprocess.CalledProcessError:
            raise RuntimeError("Error occurred while running pyreverse.")

        # Load the graph from the dot file
        try:
            with open(output_file_path, "r") as file:
                file_content = file.read()

            agraph = pgv.AGraph(string=file_content)
            self.graph = nx.DiGraph(agraph)
        except Exception as e:
            print(f"An error occurred while loading the graph: {e}")

    @staticmethod
    def _is_tool_installed(tool: str) -> bool:
        """Check if a tool is installed and accessible from the command line."""
        try:
            subprocess.run(
                [tool, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            return False


# Example Usage:
# analyzer = ClassGraphAnalyzer("/path/to/your/project")
# graph = analyzer.graph
