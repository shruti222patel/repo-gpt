import os
import pickle
from pathlib import Path

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

    def load_data(self):
        if os.path.exists(self.output_path):
            with open(self.output_path, "rb") as f:
                data = pickle.load(f)
            return pd.DataFrame(data)

    def setup(self):
        current_blocks_df = self.load_data()

        # create a dictionary of filepaths and their corresponding checksums
        embedding_code_file_checksums = (
            (
                current_blocks_df.drop_duplicates(subset=["file_checksum"])[
                    ["filepath", "file_checksum"]
                ]
                .set_index("file_checksum")
                .to_dict()["filepath"]
            )
            if current_blocks_df is not None
            else {}
        )

        code_blocks = self.extractor.extract_functions(embedding_code_file_checksums)
        df = self.processor.process(code_blocks)

        if df is not None:
            df = df._append(current_blocks_df, ignore_index=True)
            path = Path(self.output_path)
            directory = path.parent

            if not directory.exists():
                directory.mkdir(parents=True)
                print(f"Directory created: {directory}")

            # Save DataFrame as a pickle file
            with open(self.output_path, "wb") as f:
                pickle.dump(df, f)
        print("All done! ✨ 🦄 ✨")
