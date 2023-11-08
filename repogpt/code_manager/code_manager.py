import asyncio
import logging
import os
import pickle
from pathlib import Path

import pandas as pd

from repogpt.code_manager.code_dir_extractor import CodeDirectoryExtractor
from repogpt.code_manager.code_processor import CodeProcessor
from repogpt.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class CodeManager:
    def __init__(
        self,
        output_filepath: Path,
        root_directory: Path,
        openai_service: OpenAIService = None,
    ):
        self.root_directory = (
            root_directory if isinstance(root_directory, Path) else Path(root_directory)
        )
        self.output_filepath = (
            output_filepath
            if isinstance(output_filepath, Path)
            else Path(output_filepath)
        )
        self.openai_service = (
            openai_service if openai_service is not None else OpenAIService()
        )

        self.code_df = self.load_code_dataframe()
        self.directory_extractor = CodeDirectoryExtractor(
            self.root_directory, self.output_filepath, openai_service, self.code_df
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
        dataframe = pd.DataFrame()
        if os.path.exists(self.output_filepath):
            with open(self.output_filepath, "rb") as file:
                loaded_data = pickle.load(file)
            dataframe = pd.DataFrame(loaded_data)
        return dataframe

    async def setup(self):
        # Assuming extract_code_blocks_from_files is an async method
        updated_df = await self.directory_extractor.create_updated_code_df()
        await self._store_code_dataframe(updated_df)

    async def _store_code_dataframe(self, dataframe):
        output_directory = self.output_filepath.parent
        if not output_directory.exists():
            output_directory.mkdir(parents=True)
            # await logger.verbose_info(f"Directory created: {output_directory}")

        # Save DataFrame as a pickle file using asyncio executor to run the blocking I/O operation in a separate thread
        await asyncio.get_running_loop().run_in_executor(
            None, self._pickle_dump, dataframe, self.output_filepath
        )

    def _pickle_dump(self, dataframe, filepath):
        print(f"Saving dataframe to {filepath}")
        print(dataframe.head())
        with open(filepath, "wb") as file:
            pickle.dump(dataframe, file)
        print(f"Saved dataframe to {filepath}")


def test():
    # Example usage, assuming you have setup the rest of the necessary components
    CODE_ROOT_PATH = Path("/Users/shrutipatel/projects/work/repo-gpt")
    CODE_EMBEDDING_FILE_PATH = Path(CODE_ROOT_PATH / ".repogpt" / "code_embeddings.pkl")
    code_manager = CodeManager(CODE_EMBEDDING_FILE_PATH, CODE_ROOT_PATH)
    asyncio.run(code_manager.setup())


# # Usage outside the class definition
# # asyncio.run() should be called from the main entry point of the application
if __name__ == "__main__":
    test()
