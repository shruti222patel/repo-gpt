import pytest

from repo_gpt.file_handler.abstract_handler import VSCodeExtCodeLensCode
from src.repo_gpt.file_handler.generic_code_file_handler import ElixirFileHandler

handler = ElixirFileHandler()

# Define some sample Elixir inputs
SAMPLE_INPUT_TEXT_FUNCTION = """
defmodule Sample do
  def hello_world do
    IO.puts("Hello, world!")
  end
end
"""

SAMPLE_INPUT_TEXT_MODULE = """
defmodule SampleModule do
  def method_one do
    # Do something
  end
end
"""

# Define expected output for Elixir
EXPECTED_OUTPUT_FUNCTION = [
    VSCodeExtCodeLensCode(
        name="hello_world",
        start_line=2,
        end_line=5,
        # code='def hello_world do\n    IO.puts("Hello, world!")\n  end',
    )
]

EXPECTED_OUTPUT_MODULE = [
    VSCodeExtCodeLensCode(
        name="SampleModule",
        start_line=1,
        end_line=6,
        # code='defmodule SampleModule do\n  def method_one do\n    # Do something\n  end\nend',
    ),
    VSCodeExtCodeLensCode(
        name="method_one",
        start_line=2,
        end_line=5,
        # code='def method_one do\n    # Do something\n  end',
    ),
]


@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        (SAMPLE_INPUT_TEXT_FUNCTION, EXPECTED_OUTPUT_FUNCTION),
        (SAMPLE_INPUT_TEXT_MODULE, EXPECTED_OUTPUT_MODULE),
    ],
)
def test_extract_vscode_ext_codelens_elixir(tmp_path, input_text, expected_output):
    # Create a temporary file with the sample input
    p = tmp_path / "sample.ex"
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
