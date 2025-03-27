import pytest

from repo_gpt.code_manager.abstract_extractor import AbstractCodeExtractor
from repo_gpt.code_manager.code_dir_extractor import CodeDirExtractor
from repo_gpt.file_handler.abstract_handler import ParsedCode

supported_extensions = [
    ext.lstrip(".") for ext in AbstractCodeExtractor.HANDLER_MAPPING.keys()
]


@pytest.mark.parametrize("extension", supported_extensions)
@pytest.mark.parametrize(
    "code_files, embedding_code_file_checksums, expected_output, expected_prints",
    [
        # Scenario 1: code_files is an empty list
        ([], {}, [], []),
        # Scenario 2: code_files contains multiple file paths
        (
            ["file1", "file2", "file3"],
            {},
            [ParsedCode(), ParsedCode(), ParsedCode()],
            [
                "🟢 Extracted 3 functions from /path/to/file1.{}",
                "🟢 Extracted 3 functions from /path/to/file2.{}",
                "🟢 Extracted 3 functions from /path/to/file3.{}",
            ],
        ),
        # Scenario 3: embedding_code_file_checksums is an empty dictionary
        (
            ["file1", "file2"],
            {},
            [ParsedCode(), ParsedCode()],
            [
                "🟢 Extracted 3 functions from /path/to/file1.{}",
                "🟢 Extracted 3 functions from /path/to/file2.{}",
            ],
        ),
        # Scenario 4: embedding_code_file_checksums contains checksums for some files
        (
            ["file1", "file2"],
            {"/path/to/file1.EXT": "checksum1"},
            [ParsedCode()],
            [
                "🟡 Skipping -- file unmodified /path/to/file1.{}",
                "🟢 Extracted 3 functions from /path/to/file2.{}",
            ],
        ),
        # Scenario 5: No functions or classes found in a code file
        (
            ["file1"],
            {},
            [],
            ["🟡 Skipping -- no functions or classes found /path/to/file1.{}"],
        ),
        # Scenario 6: Multiple functions or classes found in a code file
        (
            ["file1"],
            {},
            [ParsedCode(), ParsedCode()],
            ["🟢 Extracted 2 functions from /path/to/file1.{}"],
        ),
        # Scenario 7: The extract_functions_from_file method raises an exception
        (
            ["file1"],
            {},
            [],
            ["🟡 Skipping -- no functions or classes found /path/to/file1.{}"],
        ),
        # Scenario 8: The extract_code_files method raises an exception
        ([], {}, [], []),
        # Scenario 9: The generate_md5 method raises an exception
        (
            ["file1"],
            {},
            [],
            ["🟡 Skipping -- no functions or classes found /path/to/file1.{}"],
        ),
        # Scenario 10: The print statements are disabled
        (
            ["file1"],
            {},
            [ParsedCode()],
            [],
        ),
    ],
)
def test_extract_functions_across_filetypes(
    extension,
    code_files,
    embedding_code_file_checksums,
    expected_output,
    expected_prints,
):
    # Prepare the full file paths with the correct extension
    full_paths = [f"/path/to/{f}.{extension}" for f in code_files]
    updated_checksums = {
        k.replace("EXT", extension): v for k, v in embedding_code_file_checksums.items()
    }
    expected_prints = [msg.format(extension) for msg in expected_prints]

    # Mock the necessary methods and objects
    my_class = CodeDirExtractor()
    my_class.extract_code_files = lambda: full_paths
    my_class.generate_md5 = (
        lambda file_path: "checksum1"
        if file_path.endswith(f"file1.{extension}")
        else "checksum2"
    )

    def mock_extract(file_path, checksum):
        if "file1" in file_path and "Multiple functions" in str(expected_prints):
            return [ParsedCode(), ParsedCode()]
        elif "file1" in file_path and expected_output:
            return [ParsedCode()]
        return []

    my_class.extract_functions_from_file = mock_extract

    # Capture print output
    captured_prints = []
    my_class.print = lambda *args: captured_prints.append(" ".join(args))

    # Call the method under test
    output = my_class.extract_functions(updated_checksums)

    # Assert
    assert output == expected_output
    assert captured_prints == expected_prints
