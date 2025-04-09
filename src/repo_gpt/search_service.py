import json
import logging
import pickle
from enum import Enum
from pathlib import Path, PosixPath
from typing import Union

import numpy as np
import pandas as pd
from Levenshtein import distance as levenshtein_distance
from rich.markdown import Markdown
from tqdm.auto import tqdm

from .console import console, pretty_print_code, verbose_print
from .file_handler.abstract_handler import ParsedCode
from .openai_service import OpenAIService
from .utils import Singleton

logger = logging.getLogger(__name__)


class CustomCodeEmbeddingDFEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, PosixPath):
            return str(obj)
        return super(CustomCodeEmbeddingDFEncoder, self).default(obj)


def convert_search_df_to_json(
    df: pd.DataFrame,
    selected_columns: list = [
        "class_name",
        "function_name",
        "code",
        "code_type",
        "summary",
        "inputs",
        "outputs",
        "filepath",
    ],
):
    df_dict = df[selected_columns].to_dict(orient="records")
    return json.dumps(df_dict, cls=CustomCodeEmbeddingDFEncoder)


class SearchService(metaclass=Singleton):
    def __init__(
        self,
        openai_service: OpenAIService,
        pickle_path: Union[Path, str] = None,
        language: str = "python",
    ):
        self.pickle_path = (
            pickle_path if isinstance(pickle_path, Path) else Path(pickle_path)
        )
        if self.pickle_path is not None and self.pickle_path.exists():
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
        similar_code_df = self.semantic_search_similar_code(code_query)
        pretty_print_code(similar_code_df, self.language)
        return similar_code_df

    def find_function_match(
        self, function_name: str, class_name: str = None, matches_to_return: int = 3
    ) -> pd.DataFrame:
        print(f"Loaded dataframe with {len(self.df)} code blocks")
        print(f"Searching for function {function_name}...")

        # Handle None values for class_name and function_name
        class_name = class_name or ""
        function_name = function_name or ""

        # Concatenate class_name and function_name for comparison
        search_name = f"{class_name}{function_name}"

        # Calculate the Levenshtein distance for the concatenated names without modifying self.df
        name_distances = self.df.apply(
            lambda row: levenshtein_distance(
                search_name, f"{row['class_name'] or ''}{row['function_name'] or ''}"
            ),
            axis=1,
        )

        # Get the indices of the smallest distances
        closest_indices = np.argsort(name_distances)[:matches_to_return]

        # Return the top matches using the indices to index into the original DataFrame
        return self.df.iloc[closest_indices]

    # def find_function_match(
    #         self, function_name: str, class_name: str = None, matches_to_return: int = 3
    # ) -> pd.DataFrame:
    #     print(f"Loaded dataframe with {len(self.df)} code blocks")
    #     print(f"Searching for function {function_name}...")
    #
    #     # Handle None values for class_name and function_name
    #     class_name = class_name or ''
    #     function_name = function_name or ''
    #
    #     # Concatenate class_name and function_name in the dataframe
    #     self.df['full_name'] = self.df['class_name'].fillna('') + self.df['function_name'].fillna('')
    #
    #     # Calculate the Levenshtein distance for the concatenated names
    #     search_name = f"{class_name}{function_name}"
    #     self.df['name_distance'] = self.df['full_name'].apply(
    #         lambda x: levenshtein_distance(search_name, x)
    #     )
    #
    #     # Sort the DataFrame by the distance and get the top matches_to_return
    #     return self.df.sort_values(by='name_distance').head(matches_to_return)

    # def semantic_search_similar_code(self, query: str, matches_to_return: int = 3):
    #     embedding = self.openai_service.get_embedding(query)
    #     logger.verbose_info("Searching for similar code...")
    #
    #     if logger.getEffectiveLevel() < logging.INFO:
    #         tqdm.pandas()
    #         self.df["similarities"] = self.df["code_embedding"].progress_apply(
    #             lambda x: x.dot(embedding)
    #         )
    #     else:
    #         self.df["similarities"] = self.df["code_embedding"].apply(
    #             lambda x: x.dot(embedding)
    #         )
    #
    #     return self.df.sort_values("similarities", ascending=False).head(
    #         matches_to_return
    #     )

    def semantic_search_similar_code(self, query: str, matches_to_return: int = 3):
        embedding = self.openai_service.get_embedding(query)
        logger.verbose_info("Searching for similar code...")

        # Calculate similarities as a separate series instead of a DataFrame column
        if logger.getEffectiveLevel() < logging.INFO:
            tqdm.pandas(desc="Processing")
            similarities = self.df["code_embedding"].progress_apply(
                lambda x: x.dot(embedding)
            )
        else:
            similarities = self.df["code_embedding"].apply(lambda x: x.dot(embedding))

        # Attach similarities as a column
        df_with_scores = self.df.copy()
        df_with_scores["similarities"] = similarities

        # Sort and return top matches
        return df_with_scores.sort_values("similarities", ascending=False).head(
            matches_to_return
        )

    def question_answer(self, question: str):
        similar_code_df = self.semantic_search_similar_code(question)
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

    def analyze_file(self, file_path: str, output_html: bool = False):
        with open(file_path, "r") as f:
            code = f.read()

        self.explain(code, output_html=output_html)

    def explain(self, code: str, output_html: bool = False):
        format = "html" if output_html else "markdown"
        try:
            explanation = self.openai_service.query_stream(
                f"""Please explain the following {self.language} function.

```{self.language}
{code}
```""",
                system_prompt=f"""You are a world-class {self.language} developer and you are explaining the following code to a junior developer. Be concise. Organize your explanation in {format}.""",
            )
            return explanation
        except Exception as e:
            return e.message
