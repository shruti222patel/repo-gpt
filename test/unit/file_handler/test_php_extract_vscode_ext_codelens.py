import pytest

from src.repo_gpt.file_handler.abstract_handler import VSCodeExtCodeLensCode
from src.repo_gpt.file_handler.generic_code_file_handler import (  # Assuming you have this handler
    PHPFileHandler,
)

handler = PHPFileHandler()

# Define some sample PHP inputs
SAMPLE_INPUT_TEXT_FUNCTION = """
<?php
function helloWorld() {
    echo "Hello, world!";
}
?>
"""

SAMPLE_INPUT_TEXT_CLASS = """
<?php
class SampleClass {
    public function methodOne() {
        // Do something
    }
}
?>
"""

# Define expected output for PHP
EXPECTED_OUTPUT_FUNCTION = [
    VSCodeExtCodeLensCode(
        name="helloWorld",
        start_line=2,
        end_line=4,
        # code='function helloWorld() {\n    echo "Hello, world!";\n}',
    )
]

EXPECTED_OUTPUT_CLASS = [
    VSCodeExtCodeLensCode(
        name="SampleClass",
        start_line=2,
        end_line=6,
        # code="class SampleClass {\n    public function methodOne() {\n        // Do something\n    }\n}",
    ),
    VSCodeExtCodeLensCode(
        name="methodOne",
        start_line=3,
        end_line=5,
        # code="public function methodOne() {\n        // Do something\n    }",
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
    p = tmp_path / "sample.php"
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
