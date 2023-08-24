import os
from abc import ABC
from enum import Enum
from typing import List, Type

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

from repo_gpt.file_handler.abstract_handler import FileHandler
from repo_gpt.file_handler.generic_code_file_handler import (
    PHPFileHandler,
    PythonFileHandler,
    TypeScriptFileHandler,
)
from repo_gpt.file_handler.generic_sql_file_handler import GenericSQLFileHandler


class LanguageHandler(Enum):
    PYTHON = PythonFileHandler
    SQL = GenericSQLFileHandler
    PHP = PHPFileHandler
    TYPESCRIPT = TypeScriptFileHandler


class AbstractCodeExtractor(ABC):
    HANDLER_MAPPING = {
        ".py": PythonFileHandler,
        ".sql": GenericSQLFileHandler,
        ".php": PHPFileHandler,
        ".ts": TypeScriptFileHandler,
    }

    def _detect_language(self, file_path):
        """Detect the coding language based on the file's extension using Pygments."""
        try:
            lexer = get_lexer_for_filename(file_path)
            return lexer.name
        except ClassNotFound:
            # This exception is raised if Pygments can't find a lexer based on the file's extension.
            return (
                f"Unknown language for file extension: {os.path.splitext(file_path)[1]}"
            )

    def get_gitignore(self) -> List[str]:
        gitignore_path = self.code_root_path / ".gitignore"
        if gitignore_path.is_file():
            with open(gitignore_path, "r") as file:
                return file.read().splitlines()
        else:
            return []

    def is_file_parsable(self, filepath: str) -> bool:
        gitignore = self.get_gitignore()
        spec = PathSpec.from_lines(GitWildMatchPattern, gitignore)
        handler_class = self.get_handler(filepath)
        if handler_class is None or spec.match_file(filepath):
            return False
        return True

    def is_dir_parsable(self, dirpath: str) -> bool:
        gitignore = self.get_gitignore()
        spec = PathSpec.from_lines(GitWildMatchPattern, gitignore)
        if spec.match_file(dirpath):
            return False
        return True

    def get_handler(self, filepath: str) -> Type[FileHandler]:
        _, file_extension = os.path.splitext(filepath)
        handler_class = self.HANDLER_MAPPING.get(file_extension)
        if handler_class is None:
            print(
                f"No handler for files with extension {file_extension}. Skipping file {filepath}"
            )
        return handler_class
