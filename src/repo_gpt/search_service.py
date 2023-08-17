import pickle
from pathlib import Path
from typing import Tuple

import pandas as pd
from rich.markdown import Markdown
from tqdm import tqdm

from .console import console, pretty_print_code
from .file_handler.abstract_handler import CodeType
from .openai_service import OpenAIService

tqdm.pandas()


class SearchService:
    def __init__(
        self, pickle_path: Path, openai_service: OpenAIService, language: str = "python"
    ):
        self.pickle_path = pickle_path
        self.refresh_df()
        self.openai_service = openai_service
        self.language = language

    def refresh_df(self):
        with open(self.pickle_path, "rb") as f:
            self.df = pickle.load(f)
            if self.df is None or self.df.empty:
                raise Exception(
                    "Dataframe is empty. Run `repo-gpt setup` to populate it."
                )

    def simple_search(self, query: str):
        # Simple query logic: print the rows where 'code' column contains the query string
        matches = self.df[self.df["code"].str.contains(query)]
        print(matches)

    def semantic_search(self, code_query: str):
        similar_code_df = self._semantic_search_similar_code(code_query)
        pretty_print_code(similar_code_df, self.language)
        return similar_code_df

    def find_function_match(
        self, function_name: str, class_name: str = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        print(f"Loaded dataframe with {len(self.df)} code blocks")
        print(f"Searching for function {function_name}...")

        # If class_name is provided, look for class matches
        class_matches = (
            self.df[
                (self.df["name"] == class_name)
                & (self.df["code_type"] == "CodeType.CLASS")
            ]
            if class_name
            else None
        )

        # Look for function matches
        function_matches = self.df[
            (self.df["name"] == function_name)
            # & ((self.df["code_type"] == "CodeType.FUNCTION") | (self.df["code_type"] == "CodeType.METHOD")) # TODO not sure why this doesn't work. I just need to switch to polars
        ]

        return function_matches, class_matches

    def _semantic_search_similar_code(self, query: str, matches_to_return: int = 3):
        embedding = self.openai_service.get_embedding(query)
        console.print("Searching for similar code...")
        self.df["similarities"] = self.df["code_embedding"].progress_apply(
            lambda x: x.dot(embedding)
        )

        return self.df.sort_values("similarities", ascending=False).head(
            matches_to_return
        )

    def question_answer(self, question: str):
        similar_code_df = self._semantic_search_similar_code(question)
        pretty_print_code(similar_code_df, self.language)

        # TODO: add code to only send X amount of tokens to OpenAI
        # concatenate all the code blocks into one string
        code = "\n".join(similar_code_df["code"].tolist())

        console.print("")

        console.print("Asking 'GPT3.5' your question...")
        # an example question about the 2022 Olympics
        ans = self.openai_service.get_answer(question, code)
        ans_md = Markdown(ans)
        console.print("🤖 Answer from `GPT3.5` 🤖")
        console.print(ans_md)

    def analyze_file(self, file_path: str):
        with open(file_path, "r") as f:
            code = f.read()
        console.print("Analyzing your code...")
        ans = self.openai_service.get_answer(
            "Please explain the following code. Review what each element of the "
            "code is doing precisely and what the author's intentions may have "
            "been. Organize your explanation as a markdown-formatted, bulleted list.",
            code,
            system_prompt=self.openai_service.ANALYSIS_SYSTEM_PROMPT,
        )
        ans_md = Markdown(ans)
        console.print("🤖 Answer from `GPT3.5` 🤖")
        console.print(ans_md)
