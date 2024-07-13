import pytest

from repogpt.file_handler.abstract_handler import VSCodeExtCodeLensCode
from repogpt.file_handler.generic_code_file_handler import PythonFileHandler

handler = PythonFileHandler()

# Define some sample inputs
SAMPLE_INPUT_TEXT_FUNCTION = """
def hello_world():
    print("Hello, world!")

@decorator
def hello_world():
    print("Hello, world!")
"""

SAMPLE_INPUT_TEXT_CLASS = """
class SampleClass:
    def method_one(self):
        pass
"""

# Define expected output
EXPECTED_OUTPUT_FUNCTION = [
    VSCodeExtCodeLensCode(
        name="hello_world",
        start_line=1,
        end_line=2,
        # code='def hello_world():\n    print("Hello, world!")',
    ),
    VSCodeExtCodeLensCode(
        name="hello_world",
        start_line=5,
        end_line=6,
        # code='def hello_world():\n    print("Hello, world!")',
    ),
]

EXPECTED_OUTPUT_CLASS = [
    VSCodeExtCodeLensCode(
        name="SampleClass",
        start_line=1,
        end_line=3,
        # code="class SampleClass:\n    def method_one(self):\n        pass",
    ),
    VSCodeExtCodeLensCode(
        name="method_one",
        start_line=2,
        end_line=3,
        # code="def method_one(self):\n        pass",
    ),
]


@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        (SAMPLE_INPUT_TEXT_FUNCTION, EXPECTED_OUTPUT_FUNCTION),
        (SAMPLE_INPUT_TEXT_CLASS, EXPECTED_OUTPUT_CLASS),
    ],
)
def test_extract_vscode_ext_codelens(tmp_path, input_text, expected_output):
    # Create a temporary file with the sample input
    p = tmp_path / "sample.py"
    p.write_text(input_text)

    # Call the function
    parsed_vs_codelens = handler.extract_vscode_ext_codelens(p)

    # Check the output
    assert isinstance(parsed_vs_codelens, list)
    assert parsed_vs_codelens == expected_output
    assert all(isinstance(code, VSCodeExtCodeLensCode) for code in parsed_vs_codelens)
    parsed_vs_codelens.sort()
    expected_output.sort()
    assert len(parsed_vs_codelens) == len(expected_output)
    assert parsed_vs_codelens == expected_output
