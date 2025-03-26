from test.it.utils import run_cli

import pytest


@pytest.mark.asyncio
async def test_cli_help():
    stdout, stderr, process = await run_cli(["help"])
    assert process.returncode == 0
    assert b"usage" in stdout.lower()
