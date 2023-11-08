import pytest

from repogpt.file_handler.abstract_handler import VSCodeExtCodeLensCode
from repogpt.file_handler.generic_code_file_handler import CSharpFileHandler

handler = CSharpFileHandler()

# Define some sample C# inputs
SAMPLE_INPUT_TEXT_METHOD = """
public class MyClass {
    public void MyMethod() {
        // method implementation
    }
}

public void GlobalFunction() {
    // function implementation
}
"""

SAMPLE_INPUT_TEXT_CLASS = """
public class SampleClass {
    public void MethodOne() {
        // method implementation
    }

    public void MethodTwo() {
        // method implementation
    }
}
"""

# Define expected output for C#
EXPECTED_OUTPUT_METHOD = [
    VSCodeExtCodeLensCode(
        name="MyClass",
        start_line=1,
        end_line=5,
        # code is omitted for simplicity
    ),
    VSCodeExtCodeLensCode(
        name="MyMethod",
        start_line=2,
        end_line=4,
        # code is omitted for simplicity
    ),
    VSCodeExtCodeLensCode(
        name="GlobalFunction",
        start_line=7,
        end_line=9,
        # code is omitted for simplicity
    ),
]

EXPECTED_OUTPUT_CLASS = [
    VSCodeExtCodeLensCode(
        name="SampleClass",
        start_line=1,
        end_line=9,
        # code is omitted for simplicity
    ),
    VSCodeExtCodeLensCode(
        name="MethodOne",
        start_line=2,
        end_line=4,
        # code is omitted for simplicity
    ),
    VSCodeExtCodeLensCode(
        name="MethodTwo",
        start_line=6,
        end_line=8,
        # code is omitted for simplicity
    ),
]


@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        (SAMPLE_INPUT_TEXT_METHOD, EXPECTED_OUTPUT_METHOD),
        (SAMPLE_INPUT_TEXT_CLASS, EXPECTED_OUTPUT_CLASS),
    ],
)
def test_extract_vscode_ext_codelens(tmp_path, input_text, expected_output):
    # Create a temporary file with the sample input
    p = tmp_path / "sample.cs"
    p.write_text(input_text)

    # Call the function
    parsed_vs_codelens = handler.extract_vscode_ext_codelens(input_text)

    # Check the output
    assert isinstance(parsed_vs_codelens, list)
    assert all(isinstance(code, VSCodeExtCodeLensCode) for code in parsed_vs_codelens)
    parsed_vs_codelens.sort(key=lambda x: x.name)
    expected_output.sort(key=lambda x: x.name)
    assert len(parsed_vs_codelens) == len(expected_output)
    assert parsed_vs_codelens == expected_output
