import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Set

import pandas as pd
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from tqdm.auto import tqdm

from ..console import verbose_print
from ..file_handler.abstract_handler import ParsedCode
from ..openai_service import EMBEDDING_MODEL
from .abstract_extractor import AbstractCodeExtractor

logger = logging.getLogger(__name__)


class CodeDirectoryExtractor(AbstractCodeExtractor):
    def __init__(
        self,
        root_directory_path: Path,
        output_filepath: Path,
        code_df: pd.DataFrame | None = None,
    ):
        self.root_directory_path = root_directory_path
        self.output_filepath = output_filepath
        self.all_code_files = self._find_all_code_files()
        self.code_df = code_df

    def generate_md5_checksum(self, file_path: str, chunk_size: int = 4096) -> str:
        file_hash = hashlib.md5()
        with open(file_path, "rb") as file:
            chunk = file.read(chunk_size)
            while chunk:
                file_hash.update(chunk)
                chunk = file.read(chunk_size)
        return file_hash.hexdigest()

    def _find_all_code_files(self) -> List[str]:
        all_code_files = []
        for current_root, directories, files in tqdm(
            os.walk(self.root_directory_path), desc="Scanning directories"
        ):
            relative_path = Path(current_root).relative_to(self.root_directory_path)

            # Ignore directories listed in .gitignore
            directories[:] = [
                dir
                for dir in directories
                if self.is_dir_parsable(os.path.join(relative_path, dir))
            ]

            for file in files:
                full_file_path = relative_path / file
                all_code_files.append(self.root_directory_path / full_file_path)
        return all_code_files

    def _map_checksum_to_filepath(self) -> Dict[str, str]:  # checksum : filepath
        return (
            self.code_df.drop_duplicates(subset=["file_checksum"])[
                ["filepath", "file_checksum"]
            ]
            .set_index("file_checksum")
            .to_dict()["filepath"]
        )

    def _map_filepath_to_checksum(self) -> Dict[str, str]:  # filepath : checksum
        # Return empty dict if DataFrame is None or empty
        if self.code_df is None or self.code_df.empty:
            return {}

        if (
            "embedding_model" not in self.code_df.columns
            or not self.code_df["embedding_model"].eq(EMBEDDING_MODEL).all()
        ):
            return {}

        # If all checks pass, return the filepath to checksum mapping
        return (
            self.code_df.drop_duplicates(subset=["file_checksum"])[
                ["filepath", "file_checksum"]
            ]
            .set_index("filepath")
            .to_dict()["file_checksum"]
        )

    def is_dir_parsable(self, dirpath: str) -> bool:
        # Check if the directory is hidden
        dirname = Path(dirpath).name
        if dirname.startswith("."):
            return False

        gitignore = self.get_gitignore()
        spec = PathSpec.from_lines(GitWildMatchPattern, gitignore)

        if spec.match_file(dirpath):
            return False

        return True

    def get_gitignore(self) -> List[str]:
        gitignore_path = self.root_directory_path / ".gitignore"
        if gitignore_path.is_file():
            with open(gitignore_path, "r") as file:
                return file.read().splitlines()
        else:
            return []

    def extract_code_blocks_from_files(self) -> (List[ParsedCode], Set[str]):
        code_file_paths = self.all_code_files
        filepath_to_checksum = self._map_filepath_to_checksum()

        parsable_extensions = AbstractCodeExtractor.get_file_extensions_with_handlers()

        extracted_blocks = []
        outdated_checksums = set()
        for code_file_path in code_file_paths:
            # logger.verbose_info(f"🟢 Processing {code_file_path}")
            current_file_checksum = self.generate_md5_checksum(code_file_path)
            existing_filepath_checksum = filepath_to_checksum.get(code_file_path, None)
            if existing_filepath_checksum == current_file_checksum:
                logger.verbose_info(f"🟡 Skipping -- file unmodified {code_file_path}")
                continue

            if code_file_path.suffix not in parsable_extensions:
                logger.verbose_info(
                    f"🟡 Skipping -- no file parser for {code_file_path}"
                )
                continue

            try:
                if existing_filepath_checksum:
                    outdated_checksums.add(existing_filepath_checksum)
                extracted_file_blocks = self._extract_code_blocks_from_single_file(
                    code_file_path, current_file_checksum
                )
            except Exception as e:
                logger.verbose_info(
                    f"🔴 Skipping -- error extracting code {code_file_path}: {str(e)}"
                )
                continue
            if not extracted_file_blocks:
                logger.verbose_info(
                    f"🟡 Skipping -- no functions or classes found {code_file_path}"
                )
            else:
                logger.verbose_info(
                    f"🟢 Extracted {len(extracted_file_blocks)} functions from {code_file_path}"
                )
            extracted_blocks.extend(extracted_file_blocks)
        return extracted_blocks, outdated_checksums

    def _extract_code_blocks_from_single_file(
        self, file_path: str, file_checksum: str
    ) -> List[ParsedCode]:
        handler_for_file = AbstractCodeExtractor.get_handler(file_path)
        extracted_blocks_for_file = []
        if handler_for_file:
            extracted_blocks_for_file = handler_for_file().extract_code(file_path)
            for block in extracted_blocks_for_file:
                block.filepath = file_path
                block.file_checksum = file_checksum

        return extracted_blocks_for_file
