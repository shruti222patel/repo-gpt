import os
from pathlib import Path

import pytest

# Initialize the handler
from src.repo_gpt.file_handler.abstract_handler import ParsedCode
from src.repo_gpt.file_handler.python_file_handler import PythonFileHandler

handler = PythonFileHandler()


script_dir = Path(os.path.dirname(os.path.realpath(__file__)))


def test_normal_operation():
    # Test Python file containing well-structured functions and classes
    parsed_code = handler.extract_code(
        script_dir / Path("./python_files/well_structured_python_file.py")
    )
    assert isinstance(parsed_code, list)
    assert all(isinstance(code, ParsedCode) for code in parsed_code)

    # Test Python file with no functions or classes
    parsed_code = handler.extract_code(
        script_dir / Path("./python_files/no_function_class_python_file.py")
    )
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0


def test_edge_cases():
    # Test empty Python file
    parsed_code = handler.extract_code(
        script_dir / Path("./python_files/empty_python_file.py")
    )
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0

    # Test non-Python file
    with pytest.raises(Exception):
        handler.extract_code(script_dir / Path("./python_files/non_python_file.txt"))

    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        handler.extract_code(script_dir / Path("./python_files/non_existent_file.py"))
