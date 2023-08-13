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
        code='function helloWorld() {\n    echo "Hello, world!";\n}',
        inputs=None,
        summary=None,
        outputs=("string",),
    ),
]

EXPECTED_PHP_CLASS_PARSED_CODE = [
    ParsedCode(
        name="TestClass",
        code_type=CodeType.CLASS,
        summary="class: TestClass\n    parent classes: ('BaseClass',)\n    method: testMethod\n    parameters: None\n    code: ...\n",
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
    parsed_code.sort(key=lambda x: x.name)
    expected_output.sort(key=lambda x: x.name)
    assert len(parsed_code) == len(expected_output)
    assert parsed_code == expected_output


def test_no_function_in_file(tmp_path):
    # Test PHP file with no functions or classes
    p = tmp_path / "no_function_class_php_file.php"
    p.write_text(
        """
    $x = 10;
    $y = 20;
    $z = $x + $y;
    """
    )
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0


def test_edge_cases(tmp_path):
    # Test empty PHP file
    p = tmp_path / "empty_php_file.php"
    p.write_text("")
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0

    # Test non-PHP file
    p = tmp_path / "non_php_file.txt"
    p.write_text("This is a text file, not a PHP file.")
    parsed_code = handler.extract_code(p)
    assert len(parsed_code) == 0

    # Test non-existent file
    p = tmp_path / "non_existent_file.php"
    with pytest.raises(FileNotFoundError):
        handler.extract_code(p)
