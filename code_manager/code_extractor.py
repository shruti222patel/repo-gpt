import hashlib
import os
import pickle
from pathlib import Path
from typing import List, Type

import pandas as pd
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from file_handler.abstract_handler import CodeBlock, FileHandler
from file_handler.handler_registry import handler_registry
from file_handler.python_file_handler import PythonFileHandler
from utils import logger


class CodeExtractor:
    handler_mapping = {".py": PythonFileHandler}

    def __init__(self, code_root_path: Path, output_path: Path):
        self.code_root_path = code_root_path
        self.output_path = output_path

    def get_handler(self, filepath: str) -> Type[FileHandler]:
        _, file_extension = os.path.splitext(filepath)
        handler_class = handler_registry.get(file_extension)
        if handler_class is None:
            print(
                f"No handler for files with extension {file_extension}. Skipping file {filepath}"
            )
        return handler_class

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
        gitignore = self.get_gitignore()
        spec = PathSpec.from_lines(GitWildMatchPattern, gitignore)

        for root, dirs, files in os.walk(self.code_root_path):
            root_path = Path(root).relative_to(self.code_root_path)

            # Skip directories listed in .gitignore
            dirs[:] = [
                d for d in dirs if not spec.match_file(os.path.join(root_path, d))
            ]

            for file in files:
                if file.endswith(".py") and not spec.match_file(
                    os.path.join(root_path, file)
                ):
                    file_path = root_path / file
                    code_files.append(self.code_root_path / file_path)

        return code_files

    def get_gitignore(self) -> List[str]:
        gitignore_path = self.code_root_path / ".gitignore"
        if gitignore_path.is_file():
            with open(gitignore_path, "r") as file:
                return file.read().splitlines()
        else:
            return []

    def extract_functions(self) -> List[CodeBlock]:
        code_files = self.extract_code_files()
        code_blocks = []
        for code_file in code_files:
            logger.info(f"Extracting functions from {code_file}")
            file_code_blocks = self.extract_functions_from_file(code_file)
            code_blocks.extend(file_code_blocks)
            logger.info(f"Extracted {len(file_code_blocks)} functions from {code_file}")
        return code_blocks

    def extract_functions_from_file(self, filepath: str) -> List[CodeBlock]:
        file_checksum = self.generate_md5(filepath)
        handler = self.get_handler(filepath)
        code_blocks = []
        if handler:
            parsed_code = handler().extract_code(filepath)
            if parsed_code:
                code_blocks = [
                    CodeBlock(
                        code=parsed.code,
                        code_type=parsed.code_type,
                        name=parsed.name,
                        filepath=filepath,
                        checksum=file_checksum,
                    )
                    for parsed in parsed_code
                ]
        return code_blocks

    def load_data(self):
        if os.path.exists(self.output_path):
            with open(self.output_path, "rb") as f:
                data = pickle.load(f)
            df = pd.DataFrame(data)
            print("Data loaded from file.")
        else:
            df = pd.DataFrame()
            print("File does not exist. Created an empty DataFrame.")
        return df
