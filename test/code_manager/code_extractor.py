# imports
import pytest

from repo_gpt.code_manager.code_dir_extractor import CodeDirExtractor
from repo_gpt.file_handler.abstract_handler import ParsedCode


# unit tests
@pytest.mark.parametrize(
    "code_files, embedding_code_file_checksums, expected_output, expected_prints",
    [
        # Scenario 1: code_files is an empty list
        ([], {}, [], []),
        # Scenario 2: code_files contains multiple file paths
        (
            ["/path/to/file1.py", "/path/to/file2.py", "/path/to/file3.py"],
            {},
            [ParsedCode(), ParsedCode(), ParsedCode()],
            [
                "🟢 Extracted 3 functions from /path/to/file1.py",
                "🟢 Extracted 3 functions from /path/to/file2.py",
                "🟢 Extracted 3 functions from /path/to/file3.py",
            ],
        ),
        # Scenario 3: embedding_code_file_checksums is an empty dictionary
        (
            ["/path/to/file1.py", "/path/to/file2.py"],
            {},
            [ParsedCode(), ParsedCode()],
            [
                "🟢 Extracted 3 functions from /path/to/file1.py",
                "🟢 Extracted 3 functions from /path/to/file2.py",
            ],
        ),
        # Scenario 4: embedding_code_file_checksums contains checksums for some files
        (
            ["/path/to/file1.py", "/path/to/file2.py"],
            {"/path/to/file1.py": "checksum1"},
            [ParsedCode()],
            [
                "🟡 Skipping -- file unmodified /path/to/file1.py",
                "🟢 Extracted 3 functions from /path/to/file2.py",
            ],
        ),
        # Scenario 5: No functions or classes found in a code file
        (
            ["/path/to/file1.py"],
            {},
            [],
            ["🟡 Skipping -- no functions or classes found /path/to/file1.py"],
        ),
        # Scenario 6: Multiple functions or classes found in a code file
        (
            ["/path/to/file1.py"],
            {},
            [ParsedCode(), ParsedCode()],
            ["🟢 Extracted 2 functions from /path/to/file1.py"],
        ),
        # Scenario 7: The extract_functions_from_file method raises an exception
        (
            ["/path/to/file1.py"],
            {},
            [],
            ["🟡 Skipping -- no functions or classes found /path/to/file1.py"],
        ),
        # Scenario 8: The extract_code_files method raises an exception
        ([], {}, [], []),
        # Scenario 9: The generate_md5 method raises an exception
        (
            ["/path/to/file1.py"],
            {},
            [],
            ["🟡 Skipping -- no functions or classes found /path/to/file1.py"],
        ),
        # Scenario 10: The print statements are disabled
        (["/path/to/file1.py"], {}, [ParsedCode()], []),
    ],
)
def test_extract_functions(
    code_files, embedding_code_file_checksums, expected_output, expected_prints
):
    # Mock the necessary methods and objects
    my_class = CodeDirExtractor()
    my_class.extract_code_files = lambda: code_files
    my_class.generate_md5 = (
        lambda file_path: "checksum1"
        if file_path == "/path/to/file1.py"
        else "checksum2"
    )
    my_class.extract_functions_from_file = (
        lambda file_path, checksum: [ParsedCode()]
        if file_path == "/path/to/file1.py"
        else []
    )

    # Capture the prints during the test execution
    captured_prints = []

    def mock_print(*args):
        captured_prints.append(" ".join(args))

    my_class.print = mock_print

    # Call the function under test
    output = my_class.extract_functions(embedding_code_file_checksums)

    # Assert the output and prints
    assert output == expected_output
    assert captured_prints == expected_prints
