# Refactored RepoUnderstandingAgent using the ParentAgent
import logging
import os

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from tqdm import tqdm

from repogpt.agents.base_agent import BaseAgent
from repogpt.file_handler.generic_code_file_handler import PythonFileHandler
from repogpt.openai_service import OpenAIService
from repogpt.search_service import SearchService, convert_search_df_to_json

# Initialize the tqdm integration with pandas


logger = logging.getLogger(__name__)


def get_gitignore_spec(root_directory):
    gitignore_file = os.path.join(root_directory, ".gitignore")
    if not os.path.exists(gitignore_file):
        return None
    with open(gitignore_file, "r") as f:
        spec = PathSpec.from_lines(GitWildMatchPattern, f)
    return spec


def is_hidden(path):
    # Check if a file or directory is hidden by checking if its name starts with a dot
    return os.path.basename(path).startswith(".")


def get_indented_directory_structure(root_directory):
    structured_output = []
    gitignore_spec = get_gitignore_spec(root_directory)

    for current_path, directories, files in os.walk(root_directory):
        # Filter out hidden directories and those in gitignore
        directories[:] = [
            d
            for d in directories
            if not is_hidden(d)
            and (
                not gitignore_spec
                or not gitignore_spec.match_file(os.path.join(current_path, d))
            )
        ]

        # Skip hidden directories in the main loop
        if is_hidden(current_path):
            continue

        depth = current_path.replace(root_directory, "").count(os.sep)
        indent = "    " * depth
        structured_output.append(f"{indent}/{os.path.basename(current_path)}")
        sub_indent = "    " * (depth + 1)

        for file in sorted(files):
            # Skip hidden files or those in gitignore
            if not is_hidden(file) and (
                not gitignore_spec
                or not gitignore_spec.match_file(os.path.join(current_path, file))
            ):
                structured_output.append(f"{sub_indent}{file}")

    return "\n".join(structured_output)


def get_relative_path_directory_structure(root_directory):
    structured_output = []
    gitignore_spec = get_gitignore_spec(root_directory)

    for current_path, directories, files in os.walk(root_directory):
        # Filter out hidden directories and those in gitignore
        directories[:] = [
            d
            for d in directories
            if not is_hidden(d)
            and (
                not gitignore_spec
                or not gitignore_spec.match_file(os.path.join(current_path, d))
            )
        ]

        # Skip hidden directories in the main loop
        if is_hidden(current_path):
            continue

        # # Convert the current directory path to a relative path from the root directory
        rel_dir = os.path.relpath(current_path, root_directory)

        # # Append the relative directory path to structured_output
        # structured_output.append(rel_dir if rel_dir != "." else "")

        for file in sorted(files):
            # Skip hidden files or those in gitignore
            if not is_hidden(file) and (
                not gitignore_spec
                or not gitignore_spec.match_file(os.path.join(current_path, file))
            ):
                # Combine the relative directory path with the file name to get the relative file path
                rel_file_path = os.path.join(rel_dir, file)
                structured_output.append(rel_file_path)

    return structured_output


def get_relative_path_current_directory_structure(current_directory, root_directory):
    structured_output = []
    gitignore_spec = get_gitignore_spec(root_directory)

    # List all items in the root directory
    items = os.listdir(current_directory)

    for item in items:
        item_path = os.path.join(current_directory, item)

        # Skip hidden items or those in gitignore
        if is_hidden(item) or (gitignore_spec and gitignore_spec.match_file(item_path)):
            continue

        # Check if the item is a file or directory and append to structured_output
        if os.path.isdir(item_path):
            structured_output.append(os.path.relpath(item_path, root_directory) + "/")
        elif os.path.isfile(item_path):
            structured_output.append(os.path.relpath(item_path, root_directory))

    return structured_output


def get_relative_path_directory_structure_string(root_directory):
    return "\n".join(get_relative_path_directory_structure(root_directory))
