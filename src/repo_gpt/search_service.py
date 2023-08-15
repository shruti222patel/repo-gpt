import pickle
from pathlib import Path
from pprint import pprint

from rich.markdown import Markdown
from rich.syntax import Syntax
from tqdm import tqdm

from .console import console
from .file_handler.abstract_handler import CodeType
from .openai_service import OpenAIService

tqdm.pandas()


class SearchService:
    def __init__(self, pickle_path: Path, openai_service: OpenAIService):
        with open(pickle_path, "rb") as f:
            self.df = pickle.load(f)
        self.openai_service = openai_service

    def simple_search(self, query: str):
        # Simple query logic: print the rows where 'code' column contains the query string
        matches = self.df[self.df["code"].str.contains(query)]
        print(matches)

    def semantic_search(self, code_query: str):
        similar_code_df = self._semantic_search_similar_code(code_query)
        self._pretty_print_code(similar_code_df)
        return similar_code_df

    def find_function_match(self, function_name: str, class_name: str = None):
        class_match = None
        function_match = None

        # If class_name is provided, look for class matches
        if class_name:
            class_matches = self.df[
                (self.df["name"] == class_name)
                & (self.df["code_type"] == CodeType.CLASS)
            ]
            if not class_matches.empty:
                class_match = class_matches.iloc[0]

        # Look for function matches
        function_matches = self.df[
            (self.df["name"] == function_name)
            & (self.df["code_type"] == CodeType.FUNCTION)
        ]
        if not function_matches.empty:
            function_match = function_matches.iloc[0]

        return function_match, class_match

    def _pretty_print_code(self, similar_code_df):
        n_lines = 7
        if pprint:
            for r in similar_code_df.iterrows():
                console.rule(f"[bold red]{str(r[1].name)}")
                print(
                    str(r[1].filepath)
                    + ":"
                    + str(r[1].name)
                    + "  distance="
                    + str(round(r[1].similarities, 3))
                )
                syntax = Syntax(
                    "\n".join(r[1].code.split("\n")[:n_lines]), "python"
                )  # TODO: make this dynamic
                console.print(syntax)

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
        self._pretty_print_code(similar_code_df)

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
