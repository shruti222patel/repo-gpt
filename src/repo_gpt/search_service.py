import json
import logging
import pickle
from enum import Enum
from pathlib import Path, PosixPath
from typing import Tuple

import pandas as pd
import tqdm
from rich.markdown import Markdown

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


def convert_search_df_to_json(df: pd.DataFrame):
    selected_columns = [
        "name",
        "code",
        "code_type",
        "summary",
        "inputs",
        "outputs",
        "filepath",
    ]
    df_dict = df[selected_columns].to_dict(orient="records")
    return json.dumps(df_dict, cls=CustomCodeEmbeddingDFEncoder)


class SearchService(metaclass=Singleton):
    def __init__(
        self,
        openai_service: OpenAIService,
        pickle_path: Path = None,
        language: str = "python",
    ):
        self.pickle_path = pickle_path
        if pickle_path is not None:
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

    def semantic_search_similar_code(self, query: str, matches_to_return: int = 3):
        embedding = self.openai_service.get_embedding(query)
        logger.verbose_info("Searching for similar code...")

        if logger.getEffectiveLevel() < logging.INFO:
            tqdm.pandas()
            self.df["similarities"] = self.df["code_embedding"].progress_apply(
                lambda x: x.dot(embedding)
            )
        else:
            self.df["similarities"] = self.df["code_embedding"].apply(
                lambda x: x.dot(embedding)
            )

        return self.df.sort_values("similarities", ascending=False).head(
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
