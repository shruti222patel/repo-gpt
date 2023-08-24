import pytest

from src.repo_gpt.file_handler.abstract_handler import VSCodeExtCodeLensCode
from src.repo_gpt.file_handler.generic_code_file_handler import (  # Assuming you have this handler
    TypeScriptFileHandler,
)

handler = TypeScriptFileHandler()

# Define some sample TypeScript inputs
SAMPLE_INPUT_TEXT_FUNCTION = """
function helloWorld(): string {
    return "Hello, world!";
}
"""

SAMPLE_INPUT_TEXT_CLASS = """
class SampleClass {
    methodOne(): void {
        // Do something
    }
}
"""

# Define expected output for TypeScript
EXPECTED_OUTPUT_FUNCTION = [
    VSCodeExtCodeLensCode(
        name="helloWorld",
        start_line=1,
        code='function helloWorld(): string {\n    return "Hello, world!";\n}',
    )
]

EXPECTED_OUTPUT_CLASS = [
    VSCodeExtCodeLensCode(
        name="SampleClass",
        start_line=1,
        code="class SampleClass {\n    methodOne(): void {\n        // Do something\n    }\n}",
    ),
    VSCodeExtCodeLensCode(
        name="methodOne",
        start_line=2,
        code="methodOne(): void {\n        // Do something\n    }",
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
    p = tmp_path / "sample.ts"
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
