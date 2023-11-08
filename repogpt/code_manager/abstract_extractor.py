import os
from abc import ABC
from enum import Enum
from typing import Set, Type

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

from repogpt.file_handler.abstract_handler import FileHandler
from repogpt.file_handler.generic_code_file_handler import (
    PHPFileHandler,
    PythonFileHandler,
    TerraformFileHandler,
    TypeScriptFileHandler,
)
from repogpt.file_handler.generic_sql_file_handler import GenericSQLFileHandler


class LanguageHandler(Enum):
    PYTHON = PythonFileHandler
    SQL = GenericSQLFileHandler
    PHP = PHPFileHandler
    TYPESCRIPT = TypeScriptFileHandler
    TERRAFORM = TerraformFileHandler


def get_language_handler_from_language_name(language: str):
    try:
        # Normalize the language string and attempt to retrieve the corresponding enum
        language_enum = LanguageHandler[language.upper()]
        return language_enum.value()
    except KeyError:
        # Handle cases where the language is not found in the enum
        print(f"Unsupported language: {language}")
        return None
        # Or raise an exception, or provide a default handler, depending on your requirements


class AbstractCodeExtractor(ABC):
    HANDLER_MAPPING = {
        ".py": PythonFileHandler,
        ".sql": GenericSQLFileHandler,
        ".php": PHPFileHandler,
        ".ts": TypeScriptFileHandler,
        ".tf": TerraformFileHandler,
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
