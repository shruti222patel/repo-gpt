import asyncio
import hashlib
import logging
import os
import time
from pathlib import Path
from typing import List, Optional, Tuple

import aiofiles
import pandas as pd
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from tqdm import tqdm

from ..console import verbose_print
from ..file_handler.abstract_handler import ParsedCode
from ..openai_service import OpenAIService
from .abstract_extractor import AbstractCodeExtractor
from .code_processor import CodeProcessor

logger = logging.getLogger(__name__)


class CodeDirectoryExtractor(AbstractCodeExtractor):
    def __init__(
        self,
        root_directory_path: Path,
        output_filepath: Path,
        openai_service: OpenAIService,
        code_df: Optional[pd.DataFrame] = None,
    ):
        self.root_directory_path = root_directory_path
        self.output_filepath = output_filepath
        self.gitignore_spec = self._load_gitignore_spec()
        self.code_df = code_df if not code_df.empty else pd.DataFrame()
        self.unmodified_code_df = None
        self.modified_files_df = None
        self.openai_service = openai_service
        self.code_processor = CodeProcessor(self.root_directory_path, openai_service)

    def _load_gitignore_spec(self) -> PathSpec:
        gitignore_path = self.root_directory_path / ".gitignore"
        if gitignore_path.is_file():
            with gitignore_path.open() as file:
                gitignore_lines = file.readlines()
            return PathSpec.from_lines(GitWildMatchPattern, gitignore_lines)
        return PathSpec.from_lines(GitWildMatchPattern, [])

    async def _create_update_code_df_initial(self):
        latest_file_checksum_df = await self.create_latest_filepath_checksums_df()
        if self.code_df.empty:
            merged_df = latest_file_checksum_df
            self.unmodified_code_df = pd.DataFrame()
            self.modified_files_df = merged_df
        else:
            merged_df = latest_file_checksum_df.merge(
                self.code_df, on=["filepath", "file_checksum"], how="left"
            )

            # DataFrame where 'code_embedding' column is NOT null
            self.unmodified_code_df = merged_df[merged_df["code_embedding"].notnull()]

            # DataFrame where 'code_embedding' column is null
            self.modified_files_df = (
                merged_df[merged_df["code_embedding"].isnull()]
                .loc[:, ["filepath", "file_checksum"]]
                .drop_duplicates()
                .reset_index(drop=True)
            )

    async def _generate_md5_checksum(
        self, file_path: Path, chunk_size: int = 4096
    ) -> str:
        file_hash = hashlib.md5()
        async with aiofiles.open(file_path, "rb") as file:
            chunk = await file.read(chunk_size)
            while chunk:
                file_hash.update(chunk)
                chunk = await file.read(chunk_size)
        return file_hash.hexdigest()

    def _generate_empty_file_md5_checksum(self) -> str:
        return hashlib.md5(b"").hexdigest()

    def _is_dir_parsable(self, dirpath: Path) -> bool:
        return not dirpath.name.startswith(".") and not self.gitignore_spec.match_file(
            str(dirpath)
        )

    def _find_all_code_files(self) -> List[Path]:
        valid_extensions = set(
            AbstractCodeExtractor.get_file_extensions_with_handlers()
        )
        all_code_files = []
        for current_root, directories, files in os.walk(self.root_directory_path):
            current_root_path = Path(current_root)
            directories[:] = [
                d for d in directories if self._is_dir_parsable(current_root_path / d)
            ]
            all_code_files.extend(
                current_root_path / f
                for f in files
                if Path(f).suffix in valid_extensions
            )
        return all_code_files

    async def create_latest_filepath_checksums_df(self) -> pd.DataFrame:
        all_code_files = self._find_all_code_files()
        # Generate checksums asynchronously for all files
        checksums = await asyncio.gather(
            *(self._generate_md5_checksum(fp) for fp in all_code_files)
        )
        # Create a DataFrame from the paths and their checksums
        df = pd.DataFrame(
            {"filepath": [str(fp) for fp in all_code_files], "file_checksum": checksums}
        )
        return df

    # This value can be tuned according to your system's capabilities
    CONCURRENT_TASK_LIMIT = 20
    UPDATE_FILE_THRESHOLD = (
        0  # Set this to the number of files that trigger async execution
    )

    async def create_updated_code_df(self) -> pd.DataFrame:
        start_time = time.time()  # Start time for performance logging
        print("Starting to create updated code dataframe.")

        await self._create_update_code_df_initial()

        empty_file_checksum = self._generate_empty_file_md5_checksum()
        valid_extensions = AbstractCodeExtractor.get_file_extensions_with_handlers()

        # Filter the modified files
        filtered_start_time = time.time()
        filtered_modified_files_df = self.modified_files_df[
            (self.modified_files_df["file_checksum"] != empty_file_checksum)
        ]
        print(
            f"Filtering modified files took {time.time() - filtered_start_time} seconds."
        )

        # Process the files
        processing_start_time = time.time()
        # Run the async code with semaphore
        semaphore = asyncio.Semaphore(self.CONCURRENT_TASK_LIMIT)
        tasks = [
            self._handle_file(semaphore, row["filepath"], row["file_checksum"])
            for _, row in filtered_modified_files_df.iterrows()
        ]
        extracted_blocks = await self._flatten_task_results(tasks)

        print(f"Processing files took {time.time() - processing_start_time} seconds.")

        # Combine the unmodified and processed code dataframes
        concatenating_start_time = time.time()
        processed_code_df = await self.code_processor.process(extracted_blocks)
        final_df = pd.concat(
            [self.unmodified_code_df, processed_code_df], ignore_index=True
        )
        print(
            f"Concatenating dataframes took {time.time() - concatenating_start_time} seconds."
        )

        total_time = time.time() - start_time
        print(f"Creating the updated code dataframe completed in {total_time} seconds.")

        return final_df

    async def _flatten_task_results(self, tasks):
        large_list = []
        for task in asyncio.as_completed(tasks):
            result = await task
            # Assuming each task returns a list of dictionaries
            large_list.extend(result)
        return large_list

    async def _handle_file(self, semaphore, file_path, file_checksum):
        async with semaphore:
            return self._handle_file_sync(file_path, file_checksum)

    def _handle_file_sync(
        self, file_path: str, file_checksum: str
    ) -> Tuple[List[ParsedCode], str]:
        handler_for_file = AbstractCodeExtractor.get_handler(file_path)
        extracted_blocks_for_file = []
        if handler_for_file:
            extracted_blocks_for_file = handler_for_file().extract_code(file_path)
            for block in extracted_blocks_for_file:
                block.filepath = file_path
                block.file_checksum = file_checksum

        return extracted_blocks_for_file
