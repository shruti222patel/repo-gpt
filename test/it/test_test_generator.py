from test.it.conftest import LANGUAGE_REPOS, LANGUAGES_TO_TEST, RepoPaths, run_cli

import pandas as pd
import pytest
from multilspy.multilspy_config import Language

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.parametrize("code_language", LANGUAGES_TO_TEST)
@pytest.mark.asyncio
async def test_cli_test_generator(
    pickle_factory, code_language: Language, tmp_path_factory
):
    if code_language.name.lower() == "sql":
        pytest.skip("Skipping test for SQL code language")
    repo_paths: RepoPaths = await pickle_factory(code_language)
    function_to_test = LANGUAGE_REPOS[code_language].function_to_check
    generated_test_file_path = (
        tmp_path_factory.getbasetemp() / f"test_{function_to_test}.txt"
    )
    assert (
        repo_paths.pickle_path.exists()
    ), f"❌ [{code_language.name}] Pickle file not found at {repo_paths}"
    assert (
        repo_paths.code_source_path.exists()
    ), f"❌ [{code_language.name}] Code source path not found at {repo_paths}"

    stdout, stderr, process = await run_cli(
        [
            "--code_root_path",
            str(repo_paths.code_source_path),
            "--pickle_path",
            str(repo_paths.pickle_path),
            "add-test",
            str(function_to_test),
            "--test_save_file_path",
            str(generated_test_file_path),
        ]
    )
    assert process.returncode == 0

    assert function_to_test in stdout.decode(
        "utf-8"
    ), f"❌ '{function_to_test}' not found in chatgpt response"

    # Check that generated file exists and has the expected contents
    assert (
        generated_test_file_path.exists()
    ), f"❌ Test file was not created at {generated_test_file_path}"

    test_contents = generated_test_file_path.read_text(encoding="utf-8")

    assert (
        function_to_test in test_contents
    ), f"❌ '{function_to_test}' not mentioned in the test file"

    assert (
        "assert" in test_contents
    ), f"❌ '{function_to_test}' not mentioned in the test file"
