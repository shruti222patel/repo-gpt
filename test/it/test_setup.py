from test.it.utils import run_cli

import pytest
from multilspy.multilspy_config import Language
from utils import cli_path, create_test_context

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_cli_help():
    stdout, stderr, process = await run_cli("--help")
    assert process.returncode == 0
    assert b"usage" in stdout.lower()


@pytest.mark.asyncio
async def test_multilspy_python_black():
    code_language = Language.PYTHON
    params = {
        "code_language": code_language,
        "repo_url": "https://github.com/psf/black/",
        "repo_commit": "f3b50e466969f9142393ec32a4b2a383ffbe5f23",
    }
    with create_test_context(params) as code_source_path:
        stdout, stderr, process = await run_cli(
            ["setup", f"--code_root_path '{code_source_path}'"]
        )
        assert process.returncode == 0
