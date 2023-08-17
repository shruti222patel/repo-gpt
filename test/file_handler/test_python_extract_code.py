import pytest

from src.repo_gpt.file_handler.abstract_handler import CodeType, ParsedCode
from src.repo_gpt.file_handler.generic_code_file_handler import PythonFileHandler

handler = PythonFileHandler()

# Define input text
SAMPLE_FUNCTION_INPUT_TEXT = """
def hello_world() -> str:
    return "Hello, world!"
"""
SAMPLE_CLASS_INPUT_TEXT = """
class TestClass(BaseClass):
    \"""This is a test class. \"""
    def test_method(self):
        \"""This is a test method. \"""
        pass
"""
# Define expected parsed code
EXPECTED_FUNCTION_PARSED_CODE = [
    ParsedCode(
        name="hello_world",
        code_type=CodeType.FUNCTION,
        code='def hello_world() -> str:\n    return "Hello, world!"',
        inputs=None,
        summary=None,
        outputs=("str",),
    ),
]

EXPECTED_CLASS_PARSED_CODE = [
    ParsedCode(
        name="TestClass",
        code_type=CodeType.CLASS,
        summary="""class: TestClass\n    parent classes: ('BaseClass',)\n\n    method: test_method\n        input parameters: ('self',)\n        output parameters: None\n        code: ...\n""",
        inputs=("BaseClass",),
        code="""class TestClass(BaseClass):\n    \"""This is a test class. \"""\n    def test_method(self):\n        \"""This is a test method. \"""\n        pass""",
        outputs=None,
    ),
    ParsedCode(
        name="test_method",
        code_type=CodeType.METHOD,
        code="""def test_method(self):\n        \"""This is a test method. \"""\n        pass""",
        inputs=("self",),
        summary=None,
        outputs=None,
    ),
]


# parameterize using extracted variables
@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        (SAMPLE_FUNCTION_INPUT_TEXT, EXPECTED_FUNCTION_PARSED_CODE),
        (SAMPLE_CLASS_INPUT_TEXT, EXPECTED_CLASS_PARSED_CODE),
    ],
)
def test_normal_operation(tmp_path, input_text, expected_output):
    p = tmp_path / "test_python_file.py"
    p.write_text(input_text)
    parsed_code = handler.extract_code(p)

    assert isinstance(parsed_code, list)
    assert all(isinstance(code, ParsedCode) for code in parsed_code)
    parsed_code.sort()
    expected_output.sort()
    assert len(parsed_code) == len(expected_output)
    assert parsed_code == expected_output


def test_no_function_in_file(tmp_path):
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
    parsed_code = handler.extract_code(p)
    assert len(parsed_code) == 0

    # Test non-existent file
    p = tmp_path / "non_existent_file.py"
    with pytest.raises(FileNotFoundError):
        handler.extract_code(p)
