import pytest

from src.repo_gpt.file_handler.abstract_handler import ParsedCode
from src.repo_gpt.file_handler.generic_code_file_handler import GenericCodeFileHandler

handler = GenericCodeFileHandler()

def test_normal_operation(tmp_path):
    # Test Python file containing well-structured functions
    p = tmp_path / "well_structured_python_file.py"
    p.write_text(
        """
    def hello_world():
        print("Hello, world!")

    class TestClass:
        \"""This is a test class. \"""
        def test_method(self):
            \"""This is a test method. \"""
            pass
    """
    )
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert all(isinstance(code, ParsedCode) for code in parsed_code)
    assert len(parsed_code) == 3
    assert set(parsed_code) == set([ParsedCode(
        name="hello_world",
        code_type="function",
        code="def hello_world():\n        print(\"Hello, world!\")",
    ), ParsedCode(
        name="TestClass",
        code_type="class",
        code="""class: TestClass\n    method: test_method\n    parameters: (self)\n    code: ...\n""",
    ), ParsedCode(
        name="test_method",
        code_type="function",
        code="""def test_method(self):\n            \"""This is a test method. \"""\n            pass""",
    )])

    # Test Python file with no functions or classes
    p = tmp_path / "no_function_class_python_file.py"
    p.write_text(
        """
    x = 10
    y = 20
    z = x + y
    """
    )
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0

def test_edge_cases(tmp_path):
    # Test empty Python file
    p = tmp_path / "empty_python_file.py"
    p.write_text("")
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0

    # Test non-Python file
    p = tmp_path / "non_python_file.txt"
    p.write_text("This is a text file, not a Python file.")
    with pytest.raises(Exception):
        handler.extract_code(p)

    # Test non-existent file
    p = tmp_path / "non_existent_file.py"
    with pytest.raises(FileNotFoundError):
        handler.extract_code(p)
