import pickle
from pathlib import Path
from pprint import pprint

from rich.syntax import Syntax
from scipy import spatial
from tqdm import tqdm

from console import console
from openai_service import OpenAIService

tqdm.pandas()


class SearchService:
    def __init__(self, pickle_path: Path):
        with open(pickle_path, "rb") as f:
            self.df = pickle.load(f)
        self.openai_service = OpenAIService()

    def simple_search(self, query: str):
        # Simple query logic: print the rows where 'code' column contains the query string
        matches = self.df[self.df["code"].str.contains(query)]
        print(matches)

    def semantic_search(self, code_query: str):
        similar_code_df = self._semantic_search_similar_code(code_query)

        n_lines = 7
        if pprint:
            for r in similar_code_df.iterrows():
                console.rule(f"[bold red]{str(r[1].name)}")
                print(
                    str(r[1].filepath)
                    + ":"
                    + str(r[1].name)
                    + "  score="
                    + str(round(r[1].similarities, 3))
                )
                syntax = Syntax(
                    "\n".join(r[1].code.split("\n")[:n_lines]), "python"
                )  # TODO: make this dynamic
                console.print(syntax)
        return similar_code_df

    def _semantic_search_similar_code(self, query: str, matches_to_return: int = 3):
        embedding = self.openai_service.get_embedding(query)
        print("Searching for similar code...")
        self.df["similarities"] = self.df["code_embedding"].progress_apply(
            lambda x: spatial.distance.cosine(x, embedding)
        )

        return self.df.sort_values("similarities", ascending=False).head(
            matches_to_return
        )

    def question_answer(self, question: str):
        similar_code_df = self._semantic_search_similar_code(question)

        # TODO: add code to only send X amount of tokens to OpenAI

        # concatenate all the code blocks into one string
        code = "\n".join(similar_code_df["code"].tolist())

        # an example question about the 2022 Olympics
        return self.openai_service.get_answer(question, code)
