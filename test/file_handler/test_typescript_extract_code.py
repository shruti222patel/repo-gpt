import pytest

from src.repo_gpt.file_handler.abstract_handler import CodeType, ParsedCode
from src.repo_gpt.file_handler.generic_code_file_handler import TypeScriptFileHandler

handler = TypeScriptFileHandler()

# Define input text for TypeScript
SAMPLE_TS_FUNCTION_INPUT_TEXT = """
function helloWorld(): string {
    return "Hello, world!";
}

export async function helloWorld(): string {
    return "Hello, world!";
}
"""

SAMPLE_TS_CLASS_INPUT_TEXT = """
class TestClass extends BaseClass {
    // This is a test class.
    testMethod(): void {
        // This is a test method.
        return;
    }
}
"""

# Define expected parsed code for TypeScript
EXPECTED_TS_FUNCTION_PARSED_CODE = [
    ParsedCode(
        name="helloWorld",
        code_type=CodeType.FUNCTION,
        code='function helloWorld(): string {\n    return "Hello, world!";\n}',
        inputs=None,
        summary=None,
        outputs=("string",),
    ),
    ParsedCode(
        name="helloWorld",
        code_type=CodeType.FUNCTION,
        code='async function helloWorld(): string {\n    return "Hello, world!";\n}',
        inputs=None,
        summary=None,
        outputs=("string",),
    ),
]

EXPECTED_TS_CLASS_PARSED_CODE = [
    ParsedCode(
        name="TestClass",
        code_type=CodeType.CLASS,
        summary="""class: TestClass\n    parent classes: ('BaseClass',)\n\n    method: testMethod\n        input parameters: None\n        output parameters: ('void',)\n        code: ...\n""",
        inputs=("BaseClass",),
        code="""class TestClass extends BaseClass {\n    // This is a test class.\n    testMethod(): void {\n        // This is a test method.\n        return;\n    }\n}""",
        outputs=None,
    ),
    ParsedCode(
        name="testMethod",
        code_type=CodeType.FUNCTION,
        code="testMethod(): void {\n        // This is a test method.\n        return;\n    }",
        inputs=None,
        summary=None,
        outputs=("void",),
    ),
]


# parameterize using extracted variables
@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        (SAMPLE_TS_FUNCTION_INPUT_TEXT, EXPECTED_TS_FUNCTION_PARSED_CODE),
        (SAMPLE_TS_CLASS_INPUT_TEXT, EXPECTED_TS_CLASS_PARSED_CODE),
    ],
)
def test_ts_normal_operation(tmp_path, input_text, expected_output):
    p = tmp_path / "test_ts_file.ts"
    p.write_text(input_text)
    parsed_code = handler.extract_code(p)

    assert isinstance(parsed_code, list)
    assert all(isinstance(code, ParsedCode) for code in parsed_code)
    assert len(parsed_code) == len(expected_output)
    parsed_code.sort()
    expected_output.sort()
    assert parsed_code == expected_output


def test_no_function_in_file(tmp_path):
    # Test TypeScript file with no functions or classes
    p = tmp_path / "no_function_class_ts_file.ts"
    code = """let x = 10;
let y = 20;
let z = x + y;"""
    p.write_text(code)
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 1
    assert parsed_code[0].code == code.strip()


def test_edge_cases(tmp_path):
    # Test empty TypeScript file
    p = tmp_path / "empty_ts_file.ts"
    p.write_text("")
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0

    # Test non-TypeScript file
    p = (
        tmp_path / "non_ts_file.txt"
    )  # This fucntion doesn't check file types only parses the text / code
    text = "This is a text file, not a TypeScript file."
    p.write_text(text)
    parsed_code = handler.extract_code(p)
    assert len(parsed_code) == 1
    assert parsed_code[0].code == text
    assert parsed_code[0].code_type == CodeType.GLOBAL

    # Test non-existent file
    p = tmp_path / "non_existent_file.ts"
    with pytest.raises(FileNotFoundError):
        handler.extract_code(p)
