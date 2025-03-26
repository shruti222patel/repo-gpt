import asyncio
import contextlib
import os
import pathlib
import shutil
import sys
import textwrap
from typing import Iterator, List, Tuple
from uuid import uuid4

from multilspy.multilspy_logger import MultilspyLogger
from multilspy.multilspy_utils import FileUtils

cli_path = pathlib.Path(__file__).resolve().parents[2] / "src" / "repo_gpt" / "cli.py"


async def run_cli(cmd: List[str]) -> Tuple[bytes, bytes, asyncio.subprocess.Process]:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise EnvironmentError("❌ OPENAI_API_KEY must be set in the test environment.")
    print(openai_api_key)
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(cli_path),
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={"OPENAI_API_KEY": openai_api_key},
    )
    stdout, stderr = await process.communicate()
    stdout_text = stdout.decode().strip()
    stderr_text = stderr.decode().strip()

    if stdout_text:
        print("🌟 Stdout:\n" + textwrap.indent(stdout_text, "  "))
    if stderr_text:
        print("⚠️  Stderr:\n" + textwrap.indent(stderr_text, "  "))
    return stdout, stderr, process


@contextlib.contextmanager
def create_test_context(params: dict) -> Iterator[str]:
    """
    Creates a test context for the given parameters.
    """

    logger = MultilspyLogger()

    user_home_dir = os.path.expanduser("~")
    multilspy_home_directory = str(pathlib.Path(user_home_dir, ".multilspy"))
    temp_extract_directory = str(pathlib.Path(multilspy_home_directory, uuid4().hex))
    try:
        os.makedirs(temp_extract_directory, exist_ok=False)
        assert params["repo_url"].endswith("/")
        repo_zip_url = params["repo_url"] + f"archive/{params['repo_commit']}.zip"
        FileUtils.download_and_extract_archive(
            logger, repo_zip_url, temp_extract_directory, "zip"
        )
        dir_contents = os.listdir(temp_extract_directory)
        assert len(dir_contents) == 1
        source_directory_path = str(
            pathlib.Path(temp_extract_directory, dir_contents[0])
        )

        yield source_directory_path
    finally:
        if os.path.exists(temp_extract_directory):
            shutil.rmtree(temp_extract_directory)
