from abc import ABC, abstractmethod

import Levenshtein
import networkx as nx


class GraphAnalyzer(ABC):
    def __init__(self, directory_path, output_file_path):
        self.directory_path = directory_path
        self.graph = None
        self._generate_and_load_graph(output_file_path)

    # Abstract methods
    @abstractmethod
    def _generate_and_load_graph(self, output_filename):
        pass

    # Private helper methods
    def _check_node_exists(self, node_name):
        if node_name not in self.graph:
            raise ValueError(f"Node with name '{node_name}' not found in the graph.")

    def _generate_hierarchical_structure(self, node, graph, visited=None):
        if visited is None:
            visited = set()
        if node in visited:
            return {node: "CYCLE"}
        visited.add(node)
        structure = {}
        for successor in graph.successors(node):
            structure[successor] = self._generate_hierarchical_structure(
                successor, graph, visited.copy()
            )
        return structure

    # Graph manipulation methods
    def set_graph(self, graph):
        self.graph = graph

    # Node relationship methods
    def get_children(self, node_name):
        self._check_node_exists(node_name)
        return list(self.graph.successors(node_name))

    def get_parents(self, node_name):
        self._check_node_exists(node_name)
        return list(self.graph.predecessors(node_name))

    def get_children_by_depth(self, node_name, depth):
        if depth < 1:
            return []
        children = self.get_children(node_name)
        for child in list(children):
            children.extend(self.get_children_by_depth(child, depth - 1))
        return list(set(children))

    def get_parents_by_depth(self, node_name, depth):
        if depth < 1:
            return []
        parents = self.get_parents(node_name)
        for parent in list(parents):
            parents.extend(self.get_parents_by_depth(parent, depth - 1))
        return list(set(parents))

    # Node search and representation methods
    def search_by_node_name(self, node_name):
        if node_name in self.graph:
            return {"name": node_name, "attributes": self.graph.nodes[node_name]}
        return None

    def fuzzy_search_by_node_name(self, search_term):
        """
        Fuzzy search for nodes by name or attributes using Levenshtein distance.

        Parameters:
            - search_term (str): The term to search for.

        Returns:
            - List of tuples where each tuple contains a node name and its distance to the search term.
              Returns the top 3 nodes with the smallest distances.
        """
        distances = []

        for node, attributes in self.graph.nodes(data=True):
            # Check distance with node name
            node_distance = Levenshtein.distance(node, search_term)
            distances.append((node, node_distance))

            # Check distance with node attributes
            for attribute, value in attributes.items():
                if isinstance(value, str):
                    attr_distance = Levenshtein.distance(value, search_term)
                    distances.append((node, attr_distance))

        # Sort by distance and pick the top 3 nodes
        distances.sort(key=lambda x: x[1])
        return distances[:3]

    def represent_node_hierarchy(
        self, node, child_levels=None, parent_levels=None, visited=None
    ):
        if visited is None:
            visited = set()
        if node in visited:
            return {node: "CYCLE"}
        visited.add(node)

        structure = {}

        if parent_levels is not None:
            structure["parents"] = self._get_parents_structure(
                node, parent_levels, visited.copy()
            )

        if child_levels is not None:
            structure["children"] = self._get_children_structure(
                node, child_levels, visited.copy()
            )

        # Filter out empty keys for clarity
        return {node: {k: v for k, v in structure.items() if v}}

    def _get_parents_structure(self, node, levels, visited):
        if levels == 0:
            return {}

        parents_structure = {}
        for parent in self.graph.predecessors(node):
            parents_structure[parent] = self.represent_node_hierarchy(
                parent,
                child_levels=None,
                parent_levels=(levels - 1),
                visited=visited.copy(),
            )

        return parents_structure

    def _get_children_structure(self, node, levels, visited):
        if levels == 0:
            return {}

        children_structure = {}
        for child in self.graph.successors(node):
            children_structure[child] = self.represent_node_hierarchy(
                child,
                child_levels=(levels - 1),
                parent_levels=None,
                visited=visited.copy(),
            )

        return children_structure

    def generate_text_representation(self, graph):
        hierarchical_representations = {}
        for node in graph.nodes():
            if not list(graph.predecessors(node)):
                hierarchical_representations[
                    node
                ] = self._generate_hierarchical_structure(node, graph)
        return hierarchical_representations

    # Graph generation methods
    def _generate_graph_by_attribute(self, attribute):
        new_graph = nx.DiGraph()
        for node, attributes in self.graph.nodes(data=True):
            current_attr = attributes.get(attribute)
            if not current_attr:
                continue
            if current_attr not in new_graph:
                new_graph.add_node(current_attr)
            for child in self.graph.successors(node):
                child_attr = self.graph.nodes[child].get(attribute)
                if child_attr and child_attr != current_attr:
                    new_graph.add_edge(current_attr, child_attr)
        return new_graph
