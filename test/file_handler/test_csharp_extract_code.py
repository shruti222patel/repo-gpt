import pytest

from repogpt.file_handler.abstract_handler import CodeType, ParsedCode
from repogpt.file_handler.generic_code_file_handler import CSharpFileHandler

handler = CSharpFileHandler()

# Define input text
SAMPLE_METHOD_INPUT_TEXT = """
public class MyClass {
    public int Add(int a, int b) {
        return a + b;
    }
}
"""
SAMPLE_CLASS_INPUT_TEXT = """
public class TestClass : BaseClass {
    public void TestMethod() {}
}
"""
# Define expected parsed code
EXPECTED_METHOD_PARSED_CODE = [
    ParsedCode(
        function_name="Add",
        class_name="MyClass",
        code_type=CodeType.METHOD,
        code="public int Add(int a, int b) {\n        return a + b;\n    }",
        inputs=("int a", "int b"),
        summary=None,
        outputs=("int",),
    ),
    ParsedCode(
        class_name="MyClass",
        function_name=None,
        code_type=CodeType.CLASS,
        summary="class: MyClass\n    method: Add\n        input parameters: ('int a', 'int b')\n        output parameters: ('int',)\n        code: ...\n",
        inputs=None,
        code="""public class MyClass {\n    public int Add(int a, int b) {\n        return a + b;\n    }\n}""",
        outputs=None,
    ),
]

EXPECTED_CLASS_PARSED_CODE = [
    ParsedCode(
        class_name="TestClass",
        function_name=None,
        code_type=CodeType.CLASS,
        summary="class: TestClass\n    parent classes: ('BaseClass',)\n    method: TestMethod\n        input parameters: ()\n        output parameters: None\n        code: ...\n",
        inputs=("BaseClass",),
        code="""public class TestClass : BaseClass {\n    public void TestMethod() {}\n}""",
        outputs=None,
    ),
    ParsedCode(
        function_name="TestMethod",
        class_name=None,
        code_type=CodeType.METHOD,
        code="public void TestMethod() {}",
        inputs=(),
        summary=None,
        outputs=None,
    ),
]


# parameterize using extracted variables
@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        (SAMPLE_METHOD_INPUT_TEXT, EXPECTED_METHOD_PARSED_CODE),
        (SAMPLE_CLASS_INPUT_TEXT, EXPECTED_CLASS_PARSED_CODE),
    ],
)
def test_normal_operation(tmp_path, input_text, expected_output):
    p = tmp_path / "test_csharp_file.cs"
    p.write_text(input_text)
    parsed_code = handler.extract_code(p)

    assert isinstance(parsed_code, list)
    assert all(isinstance(code, ParsedCode) for code in parsed_code)
    parsed_code.sort()
    expected_output.sort()
    assert len(parsed_code) == len(expected_output)
    assert parsed_code == expected_output


def test_no_function_or_class_in_file(tmp_path):
    # Test C# file with no functions or classes
    p = tmp_path / "no_function_class_csharp_file.cs"
    code = "int x = 10;\nint y = 20;\nint z = x + y;"
    p.write_text(code)
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 1
    assert parsed_code[0].code_type == CodeType.GLOBAL
    assert code.strip() in parsed_code[0].code


def test_empty_file(tmp_path):
    # Test empty C# file
    p = tmp_path / "empty_csharp_file.cs"
    p.write_text("")
    parsed_code = handler.extract_code(p)
    assert isinstance(parsed_code, list)
    assert len(parsed_code) == 0


def test_non_csharp_file(tmp_path):
    # Test non-C# file
    p = tmp_path / "non_csharp_file.txt"
    text = "This is a text file, not a C# file."
    p.write_text(text)
    parsed_code = handler.extract_code(p)
    assert len(parsed_code) == 1
    assert parsed_code[0].code_type == CodeType.GLOBAL
    assert parsed_code[0].code == text


def test_non_existent_file(tmp_path):
    # Test non-existent file
    p = tmp_path / "non_existent_file.cs"
    with pytest.raises(FileNotFoundError):
        handler.extract_code(p)
