import hashlib
import os
import pickle
from collections import namedtuple
from glob import glob
from pathlib import Path
from typing import List, Type

import pandas as pd
from tqdm import tqdm

from code_manager.code_extractor import CodeExtractor
from code_manager.code_processor import CodeProcessor

tqdm.pandas()


class CodeManager:
    def __init__(self, code_root: Path, output_path: Path):
        self.code_root = code_root
        self.output_path = output_path
        self.extractor = CodeExtractor(self.code_root, self.output_path)
        self.processor = CodeProcessor(self.code_root)

    def setup(self):
        code_blocks = self.extractor.extract_functions()
        df = self.processor.process(code_blocks)

        path = Path(self.output_path)
        directory = path.parent

        if not directory.exists():
            directory.mkdir(parents=True)
            print(f"Directory created: {directory}")

        # Save DataFrame as a pickle file
        with open(self.output_path, "wb") as f:
            pickle.dump(df, f)

    def update(self):
        current_blocks_df = self.processor.load_data()

        # create a dictionary of filepaths and their corresponding checksums
        file_checksum_dict = (
            current_blocks_df.drop_duplicates(subset=["filepath"])[
                ["filepath", "file_checksum"]
            ]
            .set_index("filepath")
            .to_dict()["file_checksum"]
        )

        # create a set of filepaths whose checksums have changed
        updated_filepaths = {
            filepath
            for filepath, checksum in file_checksum_dict.items()
            if self.extractor.generate_md5(filepath) != checksum
        }

        if updated_filepaths:
            # create a DataFrame of updated blocks
            updated_blocks = [
                block
                for filepath in updated_filepaths
                for block in self.extractor.extract_functions_from_file(filepath)
            ]
            updated_blocks_df = pd.DataFrame([vars(block) for block in updated_blocks])

            updated_blocks_df["code_embedding"] = updated_blocks_df["code"].apply(
                self.processor.get_embedding
            )

            # filter out the blocks from the current_blocks_df whose filepaths are in updated_filepaths
            current_blocks_df = current_blocks_df[
                ~current_blocks_df["filepath"].isin(updated_filepaths)
            ]

            # concatenate current_blocks_df and updated_blocks_df
            new_df = pd.concat(
                [current_blocks_df, updated_blocks_df], ignore_index=True
            )

            with open(self.output_path, "wb") as f:
                pickle.dump(new_df, f)
