import os
import pickle
from pathlib import Path
from typing import Dict

import pandas as pd
from tqdm import tqdm

from .code_extractor import CodeExtractor
from .code_processor import CodeProcessor

tqdm.pandas()


class CodeManager:
    def __init__(self, output_path: Path, code_root: Path = None):
        self.code_root = code_root
        self.output_path = output_path
        self.extractor = CodeExtractor(self.code_root, self.output_path)
        self.processor = CodeProcessor(self.code_root)

        self.current_df = self.load_data()

    def load_data(self):
        df = None
        if os.path.exists(self.output_path):
            with open(self.output_path, "rb") as f:
                data = pickle.load(f)
            df = pd.DataFrame(data)
        return df

    def setup(self):
        # create a dictionary of filepaths and their corresponding checksums
        embedding_code_file_checksums = (
            self.get_checksum_filepath_dict(self.current_df)
            if self.current_df is not None
            else None
        )
        self.parse_code_and_save_embeddings(embedding_code_file_checksums)

        print("All done! ✨ 🦄 ✨")

    def get_checksum_filepath_dict(self, df):
        return (
            df.drop_duplicates(subset=["file_checksum"])[["filepath", "file_checksum"]]
            .set_index("file_checksum")
            .to_dict()["filepath"]
        )

    def _update_or_create_post(self, df):
        df = df._append(self.current_df, ignore_index=True)
        path = Path(self.output_path)
        directory = path.parent

        if not directory.exists():
            directory.mkdir(parents=True)
            print(f"Directory created: {directory}")

        # Save DataFrame as a pickle file
        with open(self.output_path, "wb") as f:
            pickle.dump(df, f)

    def parse_code_and_save_embeddings(
        self, embedding_code_file_checksums: Dict[str, str]
    ):  # file_checksum : filepath
        code_blocks = self.extractor.extract_functions(embedding_code_file_checksums)
        df = self.processor.process(code_blocks)

        if df is not None:
            self._update_or_create_post(df)
