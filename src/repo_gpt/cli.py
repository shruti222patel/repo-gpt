#!./venv/bin/python
from pathlib import Path
from typing import Union

import configargparse

from repo_gpt import utils
from repo_gpt.agents.autogen.repo_qna import RepoQnA
from repo_gpt.logging_config import VERBOSE_INFO, configure_logging

from .code_manager.code_manager import CodeManager
from .openai_service import OpenAIService
from .search_service import SearchService
from .test_generator import TestGenerator

CODE_EMBEDDING_FILE_PATH = str(Path.cwd() / ".repo_gpt" / "code_embeddings.pkl")


def main():
    parser = configargparse.ArgParser(
        default_config_files=["pyproject.toml", ".repo_gpt/config.toml"],
        description="Code extractor and searcher",
        config_file_parser_class=configargparse.TomlConfigParser(["tool.repo_gpt"]),
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
        default=str(Path.cwd()),
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

    # Services
    openai_service = OpenAIService()

    search_service = SearchService(openai_service, args.pickle_path)

    if int(args.verbose) >= 1:
        configure_logging(VERBOSE_INFO)

    if args.command == "setup":
        code_root_path = Path(args.code_root_path)
        pickle_path = Path(args.pickle_path)
        manager = CodeManager(pickle_path, code_root_path)
        manager.setup()
    elif args.command == "search":
        update_code_embedding_file(
            search_service, args.code_root_path, args.pickle_path
        )
        _, additional_args = parser_search.parse_known_args()
        # search_service.simple_search(args.query) # simple search
        search_service.semantic_search(additional_args[0])  # semantic search
    elif args.command == "query":
        update_code_embedding_file(
            search_service, args.code_root_path, args.pickle_path
        )
        _, additional_args = parser_query.parse_known_args()
        repo_qna = RepoQnA(additional_args[0], args.code_root_path, args.pickle_path)
        repo_qna.initiate_chat()
    else:
        parser.print_help()


def update_code_embedding_file(
    search_service, root_file_path: str, code_embedding_file_path: str
) -> Union[None, str]:
    manager = CodeManager(Path(code_embedding_file_path), Path(root_file_path))
    manager.setup()
    search_service.refresh_df()


if __name__ == "__main__":
    main()
