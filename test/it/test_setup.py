import pickle
from test.it.conftest import LANGUAGE_REPOS, LANGUAGES_TO_TEST, RepoPaths

import pandas as pd
import pytest
from multilspy.multilspy_config import Language

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.parametrize("code_language", LANGUAGES_TO_TEST)
@pytest.mark.asyncio
async def test_cli_setup(pickle_factory, code_language: Language):
    repo_paths: RepoPaths = await pickle_factory(code_language)

    assert (
        repo_paths.pickle_path.exists()
    ), f"❌ [{code_language.name}] Pickle file not found at {repo_paths}"

    with repo_paths.pickle_path.open("rb") as f:
        data = pickle.load(f)

    expected_columns = {
        "function_name",
        "class_name",
        "code_type",
        "code",
        "summary",
        "inputs",
        "outputs",
        "filepath",
        "file_checksum",
        "code_embedding",
    }

    assert isinstance(data, pd.DataFrame), f"❌ [{code_language.name}] Not a DataFrame"

    missing_cols = expected_columns - set(data.columns)
    assert not missing_cols, f"❌ [{code_language.name}] Missing columns: {missing_cols}"

    # print(f"\n🧾 [{code_language.name}] Columns in the pickled DataFrame:")
    # for col in data.columns:
    #     print(f"  - {col}")

    with pd.option_context("display.max_columns", None, "display.width", 1000):
        print(f"\n🔎 [{code_language.name}] Head of the DataFrame:")
        print(data.head())

    assert (
        LANGUAGE_REPOS[code_language].function_to_check in data["function_name"].values
    ), "❌ 'fibonacci_sequence' not found in 'function_name' column"
