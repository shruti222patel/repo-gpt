import pickle
import tempfile
from pathlib import Path
from test.it.utils import create_test_context, run_cli

import pandas as pd
import pytest
from multilspy.multilspy_config import Language

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_cli_setup():
    code_language = Language.PYTHON
    params = {
        "code_language": code_language,
        "repo_url": "https://github.com/threeal/python-starter/",
        "repo_commit": "0fbc16f23cc374620a1d3f54dd8bc63d718ba735",
    }
    with create_test_context(
        params
    ) as code_source_path, tempfile.TemporaryDirectory() as tmpdir:
        pickle_path = Path(tmpdir) / "output.pickle"

        stdout, stderr, process = await run_cli(
            [
                "--code_root_path",
                str(code_source_path),
                "--pickle_path",
                str(pickle_path),
                "setup",
            ]
        )
        assert process.returncode == 0

        # Print the contents of the temp directory
        tmpdir_path = Path(tmpdir)
        contents = list(tmpdir_path.iterdir())
        print(f"📁 Contents of temp dir ({tmpdir}):")
        for path in contents:
            print(f"  - {path.name}")

        with pickle_path.open("rb") as f:
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

        if isinstance(data, pd.DataFrame):
            # ✅ Assert all expected columns exist
            missing_cols = expected_columns - set(data.columns)
            assert not missing_cols, f"❌ Missing expected columns: {missing_cols}"

            # ✅ Print columns
            print("🧾 Columns in the pickled DataFrame:")
            for col in data.columns:
                print(f"  - {col}")

            # ✅ Print head with full columns
            print("\n🔎 Head of the DataFrame:")
            with pd.option_context("display.max_columns", None, "display.width", 1000):
                print(data.head())

            # ✅ Assert "fibanacci_sequence" exists in function_name
            assert (
                "fibonacci_sequence" in data["function_name"].values
            ), "❌ 'fibonacci_sequence' not found in 'function_name' column"
        else:
            raise TypeError("❌ Pickle file did not contain a pandas DataFrame.")

        # Optional: assert that pickle file exists
        assert (
            pickle_path.exists()
        ), f"❌ Expected pickle file not found at {pickle_path}"
