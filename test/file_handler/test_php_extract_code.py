import pytest

from src.repo_gpt.file_handler.abstract_handler import CodeType, ParsedCode
from src.repo_gpt.file_handler.generic_code_file_handler import PHPFileHandler

handler = PHPFileHandler()

# Define input text for PHP
SAMPLE_PHP_FUNCTION_INPUT_TEXT = """
<?php
function helloWorld(): string {
    return "Hello, world!";
}
?>
"""

SAMPLE_PHP_CLASS_INPUT_TEXT = """
<?php
class TestClass extends BaseClass {
    /* This is a test class. */
    public function testMethod() {
        /* This is a test method. */
        return;
    }
}
?>
"""

# Define expected parsed code for PHP
EXPECTED_PHP_FUNCTION_PARSED_CODE = [
    ParsedCode(
        name="helloWorld",
        code_type=CodeType.FUNCTION,
        code='function helloWorld(): string {\n    return "Hello, world!";\n}',
        inputs=None,
        summary=None,
        outputs=("string",),
    ),
    ParsedCode(
        name=None,
        code_type=CodeType.GLOBAL,
        code="<?php\n?>",
        inputs=None,
        summary=None,
        outputs=None,
    ),
]

EXPECTED_PHP_CLASS_PARSED_CODE = [
    ParsedCode(
        name="TestClass",
        code_type=CodeType.CLASS,
        summary="""class: TestClass\n    parent classes: ('BaseClass',)\n\n    method: testMethod\n        input parameters: None\n        output parameters: None\n        code: ...\n""",
        inputs=("BaseClass",),
        code="""class TestClass extends BaseClass {\n    /* This is a test class. */\n    public function testMethod() {\n        /* This is a test method. */\n        return;\n    }\n}""",
        outputs=None,
    ),
    ParsedCode(
        name="testMethod",
        code_type=CodeType.METHOD,
        code="public function testMethod() {\n        /* This is a test method. */\n        return;\n    }",
        inputs=None,
        summary=None,
        outputs=None,
    ),
    ParsedCode(
        name=None,
        code_type=CodeType.GLOBAL,
        code="<?php\n?>",
        inputs=None,
        summary=None,
        outputs=None,
    ),
]


# parameterize using extracted variables
@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        (SAMPLE_PHP_FUNCTION_INPUT_TEXT, EXPECTED_PHP_FUNCTION_PARSED_CODE),
        (SAMPLE_PHP_CLASS_INPUT_TEXT, EXPECTED_PHP_CLASS_PARSED_CODE),
    ],
)
def test_php_normal_operation(tmp_path, input_text, expected_output):
    p = tmp_path / "test_php_file.php"
    p.write_text(input_text)
    parsed_code = handler.extract_code(p)

    assert isinstance(parsed_code, list)
    assert all(isinstance(code, ParsedCode) for code in parsed_code)
    parsed_code.sort()
    expected_output.sort()
    assert len(parsed_code) == len(expected_output)
    assert parsed_code == expected_output


def test_no_function_in_file(tmp_path):
    # Test PHP file with no functions or classes
    p = tmp_path / "no_function_class_php_file.php"
    code = """$x = 10;
$y = 20;
$z = $x + $y;"""
    p.write_text(code)
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 1
    assert parsed_code[0].code_type == CodeType.GLOBAL
    assert parsed_code[0].code == code.strip()


def test_edge_cases(tmp_path):
    # Test empty PHP file
    p = tmp_path / "empty_php_file.php"
    p.write_text("")
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0

    # Test non-PHP file
    p = (
        tmp_path / "non_php_file.txt"
    )  # the function doesn't check file types just parses text code
    text = "This is a text file, not a PHP file."
    p.write_text(text)
    parsed_code = handler.extract_code(p)
    assert len(parsed_code) == 1
    assert parsed_code[0].code_type == CodeType.GLOBAL
    assert parsed_code[0].code == text

    # Test non-existent file
    p = tmp_path / "non_existent_file.php"
    with pytest.raises(FileNotFoundError):
        handler.extract_code(p)
