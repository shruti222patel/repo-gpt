import hashlib
import os
from enum import Enum
from pathlib import Path
from typing import List, Type

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from pygments.lexers import ClassNotFound, get_lexer_for_filename
from tqdm import tqdm

from ..file_handler.abstract_handler import FileHandler, ParsedCode
from ..file_handler.generic_code_file_handler import PHPFileHandler, PythonFileHandler
from ..file_handler.sql_file_handler import SqlFileHandler
from ..utils import logger


class LanguageHandler(Enum):
    PYTHON = PythonFileHandler
    SQL = SqlFileHandler
    PHP = PHPFileHandler


class CodeExtractor:
    HANDLER_MAPPING = {
        ".py": PythonFileHandler,
        ".sql": SqlFileHandler,
        ".php": PHPFileHandler,
    }

    def __init__(self, code_root_path: Path, output_path: Path):
        self.code_root_path = code_root_path
        self.output_path = output_path

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

    def get_handler(self, filepath: str) -> Type[FileHandler]:
        _, file_extension = os.path.splitext(filepath)
        handler_class = self.HANDLER_MAPPING.get(file_extension)
        if handler_class is None:
            print(
                f"No handler for files with extension {file_extension}. Skipping file {filepath}"
            )
        return handler_class

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

    def generate_md5(self, filepath: str, chunk_size: int = 4096) -> str:
        hash = hashlib.md5()
        with open(filepath, "rb") as f:
            chunk = f.read(chunk_size)
            while chunk:
                hash.update(chunk)
                chunk = f.read(chunk_size)
        return hash.hexdigest()

    def extract_code_files(self) -> List[str]:
        code_files = []
        for root, dirs, files in tqdm(
            os.walk(self.code_root_path), desc="Scanning directories"
        ):
            root_path = Path(root).relative_to(self.code_root_path)

            # Skip directories listed in .gitignore
            dirs[:] = [
                d for d in dirs if self.is_dir_parsable(os.path.join(root_path, d))
            ]

            for file in files:
                try:
                    file_path = root_path / file
                    code_files.append(self.code_root_path / file_path)
                except Exception as e:
                    print(f"Error processing file {file}: {e}")
        return code_files

    def get_gitignore(self) -> List[str]:
        gitignore_path = self.code_root_path / ".gitignore"
        if gitignore_path.is_file():
            with open(gitignore_path, "r") as file:
                return file.read().splitlines()
        else:
            return []

    def extract_functions(
        self, embedding_code_file_checksums: dict
    ) -> List[ParsedCode]:
        code_files = (
            self.extract_code_files()
            if embedding_code_file_checksums is None
            else embedding_code_file_checksums.values()
        )
        code_blocks = []
        for code_filepath in code_files:
            print(f"🟢 Processing {code_filepath}")
            file_checksum = self.generate_md5(code_filepath)
            if (
                embedding_code_file_checksums is not None
                and file_checksum in embedding_code_file_checksums
            ):
                print(f"🟡 Skipping -- file unmodified {code_filepath}")
                continue
            file_code_blocks = self.extract_functions_from_file(
                code_filepath, file_checksum
            )
            if len(file_code_blocks) == 0:
                print(f"🟡 Skipping -- no functions or classes found {code_filepath}")
            else:
                print(
                    f"🟢 Extracted {len(file_code_blocks)} functions from {code_filepath}"
                )
            code_blocks.extend(file_code_blocks)
        return code_blocks

    def extract_functions_from_file(
        self, filepath: str, file_checksum: str
    ) -> List[ParsedCode]:
        handler = self.get_handler(filepath)
        code_blocks = []
        if handler:
            code_blocks = handler().extract_code(filepath)
            for code in code_blocks:
                code.filepath = filepath
                code.file_checksum = file_checksum

        return code_blocks
