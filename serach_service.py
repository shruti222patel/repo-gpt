import pickle
from pathlib import Path
from pprint import pprint

import pandas as pd
from scipy import spatial

from openai_service import get_embedding


class SearchService:
    def __init__(self, pickle_path: Path):
        with open(pickle_path, "rb") as f:
            self.df = pickle.load(f)

    def simple_search(self, query: str):
        # Simple query logic: print the rows where 'code' column contains the query string
        matches = self.df[self.df["code"].str.contains(query)]
        print(matches)

    def semantic_search(self, code_query: str):
        embedding = get_embedding(code_query)
        self.df["similarities"] = self.df["code_embedding"].apply(
            lambda x: spatial.distance.cosine(x, embedding)
        )

        n = 3
        n_lines = 7
        res = self.df.sort_values("similarities", ascending=False).head(n)
        if pprint:
            for r in res.iterrows():
                print(
                    str(r[1].filepath)
                    + ":"
                    + str(r[1].name)
                    + "  score="
                    + str(round(r[1].similarities, 3))
                )
                print("\n".join(r[1].code.split("\n")[:n_lines]))
                print("-" * 70)
        return res
