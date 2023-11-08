import pytest

from src.repo_gpt.file_handler.abstract_handler import CodeType, ParsedCode
from src.repo_gpt.file_handler.generic_code_file_handler import (  # Import the correct handler
    ElixirFileHandler,
)

handler = ElixirFileHandler()

# Define input text for Elixir
SAMPLE_ELIXIR_FUNCTION_INPUT_TEXT = """
defmodule MyModule do
  def hello_world do
    "Hello, world!"
  end
end
"""

SAMPLE_ELIXIR_MODULE_INPUT_TEXT = """
defmodule TestModule do
  use BaseModule

  def test_method do
    # This is a test method
  end
end
"""

# Define expected parsed code for Elixir
EXPECTED_ELIXIR_FUNCTION_PARSED_CODE = [
    ParsedCode(
        function_name="hello_world",
        class_name=None,
        code_type=CodeType.FUNCTION,
        code='def hello_world do\n    "Hello, world!"\n  end',
        inputs=None,
        summary=None,
        outputs=None,  # Placeholder
    ),
    ParsedCode(
        class_name="MyModule",
        function_name=None,
        code_type=CodeType.CLASS,  # In Elixir, it would be a module
        code=SAMPLE_ELIXIR_FUNCTION_INPUT_TEXT.strip(),
        inputs=None,
        summary=None,
        outputs=None,
    ),
]

EXPECTED_ELIXIR_MODULE_PARSED_CODE = [
    ParsedCode(
        class_name="TestModule",
        function_name=None,
        code_type=CodeType.CLASS,
        code=SAMPLE_ELIXIR_MODULE_INPUT_TEXT.strip(),
        inputs=("BaseModule",),
        summary=None,
        outputs=None,
    ),
    ParsedCode(
        function_name="test_method",
        class_name=None,
        code_type=CodeType.FUNCTION,
        code="def test_method do\n    # This is a test method\n  end",
        inputs=None,
        summary=None,
        outputs=None,
    ),
]


# parameterize using extracted variables
@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        (SAMPLE_ELIXIR_FUNCTION_INPUT_TEXT, EXPECTED_ELIXIR_FUNCTION_PARSED_CODE),
        (SAMPLE_ELIXIR_MODULE_INPUT_TEXT, EXPECTED_ELIXIR_MODULE_PARSED_CODE),
    ],
)
def test_elixir_normal_operation(tmp_path, input_text, expected_output):
    p = tmp_path / "test_elixir_file.ex"
    p.write_text(input_text)
    parsed_code = handler.extract_code(p)

    assert isinstance(parsed_code, list)
    assert all(isinstance(code, ParsedCode) for code in parsed_code)
    parsed_code.sort()
    expected_output.sort()
    assert len(parsed_code) == len(expected_output)
    assert parsed_code == expected_output
