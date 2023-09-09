import os
import pickle
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from .code_dir_extractor import CodeDirectoryExtractor
from .code_processor import CodeProcessor

tqdm.pandas()


class CodeManager:
    def __init__(self, output_filepath: Path, root_directory: Path = None):
        self.root_directory = root_directory
        self.output_filepath = output_filepath
        self.code_processor = CodeProcessor(self.root_directory)

        self.code_df = self.load_code_dataframe()
        self.directory_extractor = CodeDirectoryExtractor(
            self.root_directory, self.output_filepath, self.code_df
        )

    def display_directory_structure(self):
        structured_output = []
        for current_path, directories, files in os.walk(self.root_directory):
            depth = current_path.replace(self.root_directory, "").count(os.sep)
            indent = "    " * (depth)
            structured_output.append(f"{indent}/{os.path.basename(current_path)}")
            sub_indent = "    " * (depth + 1)
            for file in sorted(files):
                structured_output.append(f"{sub_indent}{file}")

        return "\n".join(structured_output)

    def load_code_dataframe(self):
        dataframe = None
        if os.path.exists(self.output_filepath):
            with open(self.output_filepath, "rb") as file:
                loaded_data = pickle.load(file)
            dataframe = pd.DataFrame(loaded_data)
        return dataframe

    def setup(self):
        self._extract_process_and_save_code()

        print("All done! ✨ 🦄 ✨")

    def _store_code_dataframe(self, dataframe):
        dataframe = dataframe._append(self.code_df, ignore_index=True)
        output_directory = Path(self.output_filepath).parent

        if not output_directory.exists():
            output_directory.mkdir(parents=True)
            print(f"Directory created: {output_directory}")

        # Save DataFrame as a pickle file
        with open(self.output_filepath, "wb") as file:
            pickle.dump(dataframe, file)

    def _extract_process_and_save_code(self):
        extracted_code_blocks = (
            self.directory_extractor.extract_code_blocks_from_files()
        )
        processed_dataframe = self.code_processor.process(extracted_code_blocks)

        if processed_dataframe is not None:
            self._store_code_dataframe(processed_dataframe)
