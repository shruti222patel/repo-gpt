#!./venv/bin/python
import asyncio
import os
from pathlib import Path

import configargparse

from repogpt import utils
from repogpt.agents.autogen.repo_qna import RepoQnA
from repogpt.logging_config import VERBOSE_INFO, configure_logging

from .code_manager.code_manager import CodeManager
from .openai_service import OpenAIService, is_openai_api_key_valid
from .search_service import SearchService
from .service import make_query, perform_search, setup_code_manager
from .test_generator import TestGenerator

CODE_ROOT_PATH = Path("/Users/shrutipatel/projects/work/repo-gpt")
CODE_EMBEDDING_FILE_PATH = Path(CODE_ROOT_PATH / ".repogpt" / "code_embeddings.pkl")


async def main():
    parser = configargparse.ArgParser(
        default_config_files=["pyproject.toml", ".repogpt/config.toml"],
        description="Code extractor and searcher",
        config_file_parser_class=configargparse.TomlConfigParser(["tool.repogpt"]),
    )
    parser.add_argument(
        "--pickle_path",
        type=str,
        help="Path of the pickled DataFrame to search in",
        default=CODE_EMBEDDING_FILE_PATH,
    )
    parser.add_argument(
        "--code_root_path",
        type=str,
        help="Root path of the code",
        default=CODE_ROOT_PATH,
    )
    parser.add_argument(
        "--testing_package",
        type=str,
        help="Package/library GPT should use to write tests (e.g. pytest, unittest, etc.)",
    )

    # For some reason no -v returns 2, -v returns 1, -vv returns 3, -vvv returns 5
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity level (e.g., -v, -vv, -vvv)",
    )

    subparsers = parser.add_subparsers(dest="command")

    def print_help():
        parser.print_help()

    # Sub-command to run code extraction and processing
    parser_run = subparsers.add_parser(
        "setup", help="Run code extraction and processing"
    )

    # Sub-command to search in the pickled DataFrame
    parser_search = subparsers.add_parser(
        "search", help="Search in the pickled DataFrame"
    )
    parser_search.add_argument("query", type=str, help="Query string to search for")

    # Sub-command to ask a question to the model
    parser_query = subparsers.add_parser(
        "query", help="Ask a question about the code to the model"
    )
    parser_query.add_argument("question", type=str, help="Question to ask")

    parser_help = subparsers.add_parser("help", help="Show this help message")
    parser_help.set_defaults(func=print_help)

    args, _ = parser.parse_known_args()

    if int(args.verbose) >= 1:
        configure_logging(VERBOSE_INFO)

    openai_api_key = os.environ["OPENAI_API_KEY"]

    if not is_openai_api_key_valid(openai_api_key):
        print(
            "OpenAI API key is invalid. Please set the OPENAI_API_KEY environment variable to a valid key."
        )
        exit(1)

    if args.command == "setup":
        await setup_code_manager(args.pickle_path, args.code_root_path, openai_api_key)
    elif args.command == "search":
        _, additional_args = parser_search.parse_known_args()
        search_result = await perform_search(
            additional_args[0], args.pickle_path, args.code_root_path, openai_api_key
        )
        print(search_result)
    elif args.command == "query":
        _, additional_args = parser_query.parse_known_args()
        query_result = await make_query(
            additional_args[0], args.pickle_path, args.code_root_path, openai_api_key
        )
        print(query_result)
    else:
        parser.print_help()
    print("Done!")


asyncio.run(main())
