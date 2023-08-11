import pytest

from src.repo_gpt.file_handler.abstract_handler import CodeType, ParsedCode
from src.repo_gpt.file_handler.generic_code_file_handler import PHPFileHandler

handler = PHPFileHandler()


def pretty_format_diff(diff):
    messages = []

    for key, value in diff.items():
        if key == "values_changed":
            for subkey, detail in value.items():
                old_value = detail["old_value"]
                new_value = detail["new_value"]
                messages.append(
                    f"Value changed at {subkey}: {old_value} -> {new_value}"
                )
        elif key == "iterable_item_added":
            for subkey, detail in value.items():
                messages.append(f"Item added at {subkey}: {detail}")
        elif key == "iterable_item_removed":
            for subkey, detail in value.items():
                messages.append(f"Item removed at {subkey}: {detail}")
        # Add more cases for other types of differences as needed

    return "\n".join(messages)


def test_normal_operation(tmp_path):
    # Test PHP file containing well-structured functions and classes
    p = tmp_path / "well_structured_php_file.php"
    # TODO: add base class TestClass extends from
    p.write_text(
        """
    <?php
    function helloWorld() {
        echo "Hello, world!";
    }

    class TestClass extends BaseClass {
        /* This is a test class. */
        public function testMethod() {
            /* This is a test method. */
            return;
        }
    ?>
    """
    )
    parsed_code = handler.extract_code(p)

    expected_parsed_code = [
        ParsedCode(
            name="helloWorld",
            code_type=CodeType.FUNCTION,
            code='function helloWorld() {\n        echo "Hello, world!";\n    }',
            inputs=(),
        ),
        ParsedCode(
            name="TestClass",
            code_type=CodeType.CLASS,
            code="class: TestClass\n    parent classes: ('BaseClass',)\n    method: testMethod\n    parameters: ()\n    code: ...\n",
            inputs=("BaseClass",),
        ),
        ParsedCode(
            name="testMethod",
            code_type=CodeType.FUNCTION,
            code="public function testMethod() {\n            /* This is a test method. */\n            return;\n        }",
            inputs=(),
        ),
    ]

    # Check if both lists are of type 'list' and contain objects of type 'ParsedCode'
    assert isinstance(parsed_code, list)
    assert all(isinstance(code, ParsedCode) for code in parsed_code)

    # Sort both parsed_code and expected_parsed_code by the 'name' attribute
    sorted_parsed_code = sorted(parsed_code, key=lambda x: x.name)
    sorted_expected_parsed_code = sorted(expected_parsed_code, key=lambda x: x.name)

    for i, j in zip(sorted_parsed_code, sorted_expected_parsed_code):
        assert i == j, f"Expected: {j}\nGot: {i}"

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
