import os
from abc import ABC
from enum import Enum
from typing import Set, Type

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

    @staticmethod
    def get_file_extensions_with_handlers() -> Set[str]:
        return AbstractCodeExtractor.HANDLER_MAPPING.keys()

    @staticmethod
    def detect_language(file_path):
        """Detect the coding language based on the file's extension using Pygments."""
        try:
            lexer = get_lexer_for_filename(file_path)
            return lexer.name
        except ClassNotFound:
            # This exception is raised if Pygments can't find a lexer based on the file's extension.
            return (
                f"Unknown language for file extension: {os.path.splitext(file_path)[1]}"
            )

    @staticmethod
    def get_handler(filepath: str) -> Type[FileHandler]:
        _, file_extension = os.path.splitext(filepath)
        handler_class = AbstractCodeExtractor.HANDLER_MAPPING.get(file_extension)
        if handler_class is None:
            print(
                f"No handler for files with extension {file_extension}. Skipping file {filepath}"
            )
        return handler_class
