#!./venv/bin/python

# Initialize and run code extractor
import argparse
import os
import pickle
from pathlib import Path

from code_manager.code_extractor import CodeExtractor
from code_manager.code_manager import CodeManager
from code_manager.code_processor import CodeProcessor
from serach_service import SearchService

CODE_EMBEDDING_FILE_PATH = str(Path.cwd() / ".repo_gpt" / "code_embeddings.pkl")


def main():
    parser = argparse.ArgumentParser(description="Code extractor and searcher")
    subparsers = parser.add_subparsers(dest="command")

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

    args = parser.parse_args()

    if args.command == "setup":
        root_path = Path(args.root_path)
        output_path = Path(args.output_path)
        manager = CodeManager(root_path, output_path)
        manager.setup()
    elif args.command == "search":
        search_service = SearchService(args.pickle_path)
        search_service.simple_search(args.query, args.pickle_path)


if __name__ == "__main__":
    main()
