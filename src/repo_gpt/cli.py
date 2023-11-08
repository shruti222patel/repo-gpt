#!./venv/bin/python
import os
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

    # Sub-command to analyze a file
    analyze_file = subparsers.add_parser("analyze", help="Analyze a file")
    analyze_file.add_argument("file_path", type=str, help="File to analyze")

    # Sub-command to explain a file
    explain_code = subparsers.add_parser("explain", help="Explain a code snippet")
    explain_code.add_argument(
        "--language", default="", type=str, help="Language of the code"
    )
    explain_code.add_argument("--code", type=str, help="Code you want to explain")

    # Sub-command to analyze a file
    add_test = subparsers.add_parser("add-test", help="Add tests for existing function")
    add_test.add_argument(
        "function_name", type=str, help="Name of the function you'd like to test"
    )
    add_test.add_argument(
        "--file_name",
        type=str,
        help="Name of the file the function is found in. This is helpful if there are many functions with the same "
        "name. If this isn't specified, I assume the function name is unique and I'll create tests for the first "
        "matching function I find. When a file_name is passed, I will assume the function name is unique in the "
        "file, and write tests for the first function I find with the same name in the file.",
        default="",
    )
    add_test.add_argument(
        "--test_save_file_path",
        type=str,
        help="Filepath to save the generated tests to",
    )

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
    elif args.command == "explain":
        update_code_embedding_file(
            search_service, args.code_root_path, args.pickle_path
        )
        _, additional_args = explain_code.parse_known_args()
        search_service.explain(additional_args[0])
    elif args.command == "analyze":  # TODO change to explain function
        update_code_embedding_file(
            search_service, args.code_root_path, args.pickle_path
        )
        _, additional_args = analyze_file.parse_known_args()
        search_service.analyze_file(additional_args[0])
    elif args.command == "explain":
        search_service = SearchService(openai_service, language=args.language)
        _, additional_args = explain_code.parse_known_args()
        return search_service.explain(additional_args[0])
    # elif args.command == "add-test":
    #     update_code_embedding_file(
    #         search_service, args.code_root_path, args.pickle_path
    #     )
    #     code_manager = CodeManager(Path(args.pickle_path), Path(args.code_root_path))
    #     # Look for the function name in the embedding file
    #     _, additional_args = add_test.parse_known_args()
    #     # print(additional_args)
    #
    #     print("Adding tests is temporarily disabled due to a bug in the cli parser.")
    #     add_tests(
    #         search_service,
    #         code_manager,
    #         args.function_name,
    #         args.test_save_file_path,
    #         args.testing_package,
    #     )
    else:
        parser.print_help()


def update_code_embedding_file(
    search_service, root_file_path: str, code_embedding_file_path: str
) -> Union[None, str]:
    manager = CodeManager(Path(code_embedding_file_path), Path(root_file_path))
    manager.setup()
    search_service.refresh_df()


def add_tests(
    search_service,
    code_manager,
    function_name,
    test_save_file_path,
    testing_package,
):
    # TODO: add language & test framework from config file
    # Check file path isn't a directory
    if os.path.isdir(test_save_file_path):
        print(
            f"Error: {test_save_file_path} is a directory. Please specify a file path."
        )
        return

    # TODO: check this. it seems wrong
    code = update_code_embedding_file(search_service, code_manager, function_name)

    # Save gpt history
    # Ask gpt to explain the function
    test_generator = TestGenerator(
        code,
        language="python",
        unit_test_package=testing_package,
        debug=True,
    )
    unit_tests = test_generator.unit_tests_from_function()

    print(f"Writing generated unit_tests to {test_save_file_path}...")
    # Save code to file
    if test_save_file_path is not None:
        with open(test_save_file_path, "a") as f:
            f.write(unit_tests)


if __name__ == "__main__":
    main()
