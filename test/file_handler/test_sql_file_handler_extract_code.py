import pytest

from repo_gpt.file_handler.abstract_handler import CodeType, ParsedCode
from repo_gpt.file_handler.generic_sql_file_handler import GenericSQLFileHandler

handler = GenericSQLFileHandler()


def test_single_sql_statement(tmp_path):
    # Create a file with a single SQL statement
    d = tmp_path / "single"
    d.mkdir()
    p = d / "single.sql"
    p.write_text("SELECT * FROM table;")
    # Test the function
    result = handler.extract_code(p)
    assert len(result) == 1
    assert result[0] == ParsedCode(
        function_name=None,
        class_name=None,
        code_type=CodeType.SELECT,
        code="SELECT * FROM table",
        inputs=None,
        summary=None,
        outputs=None,
    )


def test_multiple_sql_statements(tmp_path):
    # Create a file with multiple SQL statements
    d = tmp_path / "multiple"
    d.mkdir()
    p = d / "multiple.sql"
    p.write_text("SELECT * FROM table; INSERT INTO table VALUES (1, 2, 3);")
    # Test the function
    result = handler.extract_code(p)
    assert len(result) == 2
    assert result[0] == ParsedCode(
        function_name=None,
        class_name=None,
        code_type=CodeType.SELECT,
        code="SELECT * FROM table",
        inputs=None,
        summary=None,
        outputs=None,
    )
    # Bug with sqlglot: the second statement is not parsed correctly
    # assert result[1] == ParsedCode(name=None, code_type=CodeType.INSERT, code="INSERT INTO table VALUES (1, 2, 3)")
    assert result[1] == ParsedCode(
        function_name=None,
        class_name=None,
        code_type=CodeType.INSERT,
        code="INSERT INTO table VALUES (1, 2, 3)",
        inputs=None,
        summary=None,
        outputs=None,
    )


def test_nested_sql_statements(tmp_path):
    # Create a file with nested SQL statements
    d = tmp_path / "nested"
    d.mkdir()
    p = d / "nested.sql"
    p.write_text("SELECT * FROM (SELECT id FROM table);")
    # Test the function
    result = handler.extract_code(p)
    assert len(result) == 1
    assert result[0] == ParsedCode(
        function_name=None,
        class_name=None,
        code_type=CodeType.SELECT,
        code="SELECT * FROM (SELECT id FROM table)",
        inputs=None,
        summary=None,
        outputs=None,
    )


def test_comments_in_sql_file(tmp_path):
    # Create a file with SQL statements and comments
    d = tmp_path / "comments"
    d.mkdir()
    p = d / "comments.sql"
    p.write_text(
        "SELECT * FROM table; -- This is a comment\nINSERT INTO table VALUES (1, 2, 3);"
    )
    # Test the function
    result = handler.extract_code(p)
    assert len(result) == 2
    assert result[0] == ParsedCode(
        function_name=None,
        class_name=None,
        code_type=CodeType.SELECT,
        code="SELECT * FROM table",
        inputs=None,
        summary=None,
        outputs=None,
    )
    # Bug with sqlglot: the second statement is not parsed correctly
    # assert result[1] == ParsedCode(name=None, code_type=CodeType.INSERT, code="INSERT INTO table VALUES (1, 2, 3)")
    assert result[1] == ParsedCode(
        function_name=None,
        class_name=None,
        code_type=CodeType.INSERT,
        code="INSERT INTO table VALUES (1, 2, 3)",
        inputs=None,
        summary=None,
        outputs=None,
    )


def test_incorrect_sql_syntax(tmp_path):
    # Create a file with incorrect SQL syntax
    d = tmp_path / "incorrect"
    d.mkdir()
    p = d / "incorrect.py"
    p.write_text("SELECT FROM table;")
    # Test the function, expect a SQLGlotError to be raised
    result = handler.extract_code(p)
    assert len(result) == 1
    assert result[0] == ParsedCode(
        function_name=None,
        class_name=None,
        code_type=CodeType.SELECT,
        code="SELECT FROM table",
        inputs=None,
        summary=None,
        outputs=None,
    )
