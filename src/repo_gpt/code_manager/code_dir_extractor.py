import hashlib
import os
from pathlib import Path
from typing import List

from tqdm import tqdm

from ..file_handler.abstract_handler import ParsedCode
from .abstract_extractor import AbstractCodeExtractor


class CodeDirExtractor(AbstractCodeExtractor):
    def __init__(self, code_root_path: Path, output_path: Path):
        self.code_root_path = code_root_path
        self.output_path = output_path

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
                file_path = root_path / file
                code_files.append(self.code_root_path / file_path)
        return code_files

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
            try:
                file_code_blocks = self.extract_functions_from_file(
                    code_filepath, file_checksum
                )
            except Exception as e:
                # logger.error(f"Error extracting code from {code_filepath}: {e}")
                print(f"🔴 Skipping -- error extracting code {code_filepath}")
                continue
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
