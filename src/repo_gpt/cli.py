#!./venv/bin/python

import argparse
from pathlib import Path

from .code_manager.code_manager import CodeManager
from .openai_service import OpenAIService
from .search_service import SearchService

CODE_EMBEDDING_FILE_PATH = str(Path.cwd() / ".repo_gpt" / "code_embeddings.pkl")


def main():
    parser = argparse.ArgumentParser(description="Code extractor and searcher")
    subparsers = parser.add_subparsers(dest="command")

    def print_help(*args):
        parser.print_help()

    # Sub-command to run code extraction and processing
    parser_run = subparsers.add_parser(
        "setup", help="Run code extraction and processing"
    )
    parser_run.add_argument(
        "--root_path", type=str, help="Root path of the code", default=str(Path.cwd())
    )
    parser_run.add_argument(
        "--output_path",
        type=str,
        help="Output path for the pickled DataFrame",
        default=CODE_EMBEDDING_FILE_PATH,
    )

    # Sub-command to search in the pickled DataFrame
    parser_search = subparsers.add_parser(
        "search", help="Search in the pickled DataFrame"
    )
    parser_search.add_argument("query", type=str, help="Query string to search for")
    parser_search.add_argument(
        "--pickle_path",
        type=str,
        help="Path of the pickled DataFrame to search in",
        default=CODE_EMBEDDING_FILE_PATH,
    )

    # Sub-command to ask a question to the model
    parser_query = subparsers.add_parser(
        "query", help="Ask a question about the code to the model"
    )
    parser_query.add_argument("question", type=str, help="Question to ask")
    parser_query.add_argument(
        "--pickle_path",
        type=str,
        help="Path of the pickled DataFrame to search in",
        default=CODE_EMBEDDING_FILE_PATH,
    )

    # Sub-command to analyze a file
    analyze_file = subparsers.add_parser("analyze", help="Analyze a file")
    analyze_file.add_argument("file_path", type=str, help="File to analyze")
    analyze_file.add_argument(
        "--pickle_path",
        type=str,
        help="Path of the pickled DataFrame to search in",
        default=CODE_EMBEDDING_FILE_PATH,
    )

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

    add_test.add_argument(
        "--testing_package",
        type=str,
        help="Package/library GPT should use to write tests (e.g. pytest, unittest, etc.)",
    )
    add_test.add_argument(
        "--pickle_path",
        type=str,
        help="Path of the pickled DataFrame to search in",
        default=CODE_EMBEDDING_FILE_PATH,
    )

    parser_help = subparsers.add_parser("help", help="Show this help message")
    parser_help.set_defaults(func=print_help)

    args = parser.parse_args()

    # Services
    openai_service = OpenAIService()
    search_service = SearchService(args.pickle_path, openai_service)

    if args.command == "setup":
        root_path = Path(args.root_path)
        output_path = Path(args.output_path)
        manager = CodeManager(root_path, output_path)
        manager.setup()
    elif args.command == "search":
        # search_service.simple_search(args.query) # simple search
        search_service.semantic_search(args.query)  # semantic search
    elif args.command == "query":
        search_service.question_answer(args.question)
    elif args.command == "analyze":
        search_service.analyze_file(args.file_path)
    elif args.command == "add-test":
        # Look for the function name in the embedding file
        add_tests(
            search_service,
            openai_service,
            args.function_name,
            args.test_save_file_path,
            args.testing_package,
        )
    elif args.command == "add-code":
        # Prompt GPT to create tests

        # LOOP -- 3 times before erroring out
        # Prompt GPT to write code

        # Evaluate code based on tests

        # Self reflect
        pass
    elif args.command == "coder-mode":
        # Give access to code modification functions
        pass
    else:
        parser.print_help()


def add_tests(
    search_service, openai_service, function_name, test_save_file_path, testing_package
):
    # Find the function via the search service
    function_to_test = search_service.search(function_name)
    # Check if function is found
    if function_to_test is None:
        print(f"Function {function_name} not found.")
        return

    # Save gpt history
    # Ask gpt to explain the function
    code = openai_service.unit_tests_from_function(
        function_to_test, unit_test_package=testing_package
    )  # TODO: add language & test framework

    # Save code to file
    if test_save_file_path is not None:
        with open(test_save_file_path, "w") as f:
            f.write(code)


if __name__ == "__main__":
    main()
