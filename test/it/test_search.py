from test.it.conftest import LANGUAGES_TO_TEST, RepoPaths, run_cli

import pytest
from multilspy.multilspy_config import Language

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.parametrize("code_language", LANGUAGES_TO_TEST)
@pytest.mark.asyncio
async def test_cli_search(pickle_factory, code_language: Language):
    repo_paths: RepoPaths = await pickle_factory(code_language)

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
            "search",
            "How do I set up the repo locally?",
        ]
    )
    print(stderr)
    assert process.returncode == 0
