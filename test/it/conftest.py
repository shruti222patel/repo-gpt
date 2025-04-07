import asyncio
import dataclasses
import os
import pathlib
import pickle
import sys
import textwrap
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import pytest
from multilspy.multilspy_logger import MultilspyLogger
from multilspy.multilspy_utils import FileUtils

from repo_gpt.code_manager.abstract_extractor import Language


@dataclasses.dataclass(frozen=True)
class RepoConfig:
    repo_url: str
    repo_commit: str
    file_to_analyze: str
    function_to_check: Optional[str] = None


LANGUAGE_REPOS: dict[Language, RepoConfig] = {
    Language.PYTHON: RepoConfig(
        repo_url="https://github.com/threeal/python-starter/",
        repo_commit="0fbc16f23cc374620a1d3f54dd8bc63d718ba735",
        file_to_analyze="lib/my_fibonacci/sequence.py",
        function_to_check="fibonacci_sequence",
    ),
    Language.PHP: RepoConfig(
        repo_url="https://github.com/panique/mini3/",
        repo_commit="34a2867e8175319074e9ff122227e34c1e428a8f",
        file_to_analyze="application/Controller/ErrorController.php",
        function_to_check="splitUrl",
    ),
    Language.TYPESCRIPT: RepoConfig(
        repo_url="https://github.com/jellydn/typescript-mini-starter/",
        repo_commit="7ec7b47640dfae1dc988b25ac11a0f062f1c46d5",
        file_to_analyze="src/index.ts",
        function_to_check="sum",
    ),
    Language.SQL: RepoConfig(
        repo_url="https://github.com/dbt-labs/jaffle-shop/",
        repo_commit="0bbd774b8a543151249e4a9184876d839be5651a",
        file_to_analyze="models/staging/stg_products.sql",
    ),
}


LANGUAGES_TO_TEST = LANGUAGE_REPOS.keys()

cli_path = pathlib.Path(__file__).resolve().parents[2] / "src" / "repo_gpt" / "cli.py"


@dataclasses.dataclass
class RepoPaths:
    code_source_path: Path
    pickle_path: Path


async def run_cli(cmd: List[str]) -> Tuple[bytes, bytes, asyncio.subprocess.Process]:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise EnvironmentError("❌ OPENAI_API_KEY must be set in the test environment.")
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


def setup_pickle_factory(tmp_path_factory):
    cache = {}

    def get_repo_cache_path(
        repo_url: str, repo_commit: str, base_cache_dir: pathlib.Path
    ) -> pathlib.Path:
        key = f"{repo_commit}"
        return base_cache_dir / f"{key}_code"

    async def _setup_pickle(code_language: Language) -> RepoPaths:
        if code_language in cache:
            return cache[code_language]

        base_tmp = tmp_path_factory.mktemp("pickles", numbered=True)
        pickle_path = base_tmp / f"{code_language.value}_repogpt.pickle"

        base_cache_dir = tmp_path_factory.getbasetemp()
        logger = MultilspyLogger()

        if code_language not in LANGUAGE_REPOS:
            raise ValueError(f"Unsupported language: {code_language.value}")

        repo_url = LANGUAGE_REPOS[code_language].repo_url
        repo_commit = LANGUAGE_REPOS[code_language].repo_commit

        code_source_path = get_repo_cache_path(repo_url, repo_commit, base_cache_dir)

        if not code_source_path.exists():
            os.makedirs(code_source_path, exist_ok=True)

            assert repo_url.endswith("/")
            repo_zip_url = repo_url + f"archive/{repo_commit}.zip"
            FileUtils.download_and_extract_archive(
                logger, repo_zip_url, str(code_source_path), "zip"
            )

            dir_contents = os.listdir(code_source_path)
            assert len(dir_contents) == 1
            extracted_dir = pathlib.Path(code_source_path, dir_contents[0])
            code_source_path = extracted_dir

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
        assert pickle_path.exists()

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
            missing = expected_columns - set(data.columns)
            assert not missing, f"❌ Missing columns: {missing}"
        else:
            raise TypeError("❌ Pickle did not contain a DataFrame.")

        repo_paths = RepoPaths(code_source_path, Path(pickle_path))

        cache[code_language] = repo_paths

        return repo_paths

    return _setup_pickle


@pytest.fixture(scope="session")
def pickle_factory(tmp_path_factory):
    return setup_pickle_factory(tmp_path_factory)
