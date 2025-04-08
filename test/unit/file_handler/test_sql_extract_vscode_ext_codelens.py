import pytest

from repo_gpt.file_handler.abstract_handler import VSCodeExtCodeLensCode
from repo_gpt.file_handler.generic_sql_file_handler import GenericSQLFileHandler

handler = GenericSQLFileHandler()


def test_single_sql_statement(tmp_path):
    # Create a file with a single SQL statement
    d = tmp_path / "single"
    d.mkdir()
    p = d / "single.sql"
    p.write_text("SELECT * FROM table;")

    # Test the function
    result = handler.extract_vscode_ext_codelens(p)

    assert len(result) == 1
    assert result[0] == VSCodeExtCodeLensCode(
        name="select",
        # code="SELECT * FROM table",
        start_line=0,
        end_line=0,
    )


@pytest.fixture
def sql_file(tmp_path):
    # Setup: Create a file with multiple SQL statements with varied formatting
    d = tmp_path / "multiple"
    d.mkdir()
    p = d / "multiple.sql"
    p.write_text(
        """
-- CTE (Common Table Expression)
WITH CTE_Sales AS (
    SELECT
        product_id
    FROM
        sales
    GROUP BY
        product_id
)

-- SELECT statement using the CTE
SELECT
    p.product_name
FROM
    products p
WHERE
    c.total_sales > 1000;

-- UPDATE statement
UPDATE products
SET product_price = product_price * 0.9
WHERE product_id IN (SELECT product_id FROM CTE_Sales WHERE total_sales < 500);

-- DELETE statement
DELETE FROM sales
WHERE sale_date < '2022-01-01';

-- INSERT statement
INSERT INTO products (product_name, product_price)
VALUES ('New Product', 19.99);

-- Function
CREATE OR REPLACE FUNCTION get_total_sales(product_id INT) RETURNS FLOAT AS $$
BEGIN
    RETURN (
        SELECT SUM(sale_amount)
        FROM sales
        WHERE sales.product_id = get_total_sales.product_id
    );
END;
$$ LANGUAGE plpgsql;

-- Call the function
SELECT get_total_sales(5);
    """
    )
    return p


def test_cte_extraction(sql_file):
    result = handler.extract_vscode_ext_codelens(sql_file)
    assert result[0].name == "select"
    # assert "WITH CTE_Sales AS" in result[0].code
    assert result[0].start_line == 2
    assert result[0].end_line == 17


def test_update_extraction(sql_file):
    result = handler.extract_vscode_ext_codelens(sql_file)
    assert result[1].name == "update"
    # assert "UPDATE products" in result[1].code
    assert result[1].start_line == 20
    assert result[1].end_line == 22


def test_delete_extraction(sql_file):
    result = handler.extract_vscode_ext_codelens(sql_file)
    assert result[2].name == "delete"
    # assert "DELETE FROM sales" in result[2].code
    assert result[2].start_line == 25
    assert result[2].end_line == 26


def test_insert_extraction(sql_file):
    result = handler.extract_vscode_ext_codelens(sql_file)
    assert result[3].name == "insert"
    # assert "INSERT INTO products" in result[3].code
    assert result[3].start_line == 29
    assert result[3].end_line == 30


def test_function_extraction(sql_file):
    result = handler.extract_vscode_ext_codelens(sql_file)
    assert result[4].name == "function"
    # assert "CREATE OR REPLACE FUNCTION get_total_sales" in result[4].code
    assert result[4].start_line == 33
    assert result[4].end_line == 41


def test_function_call_extraction(sql_file):
    result = handler.extract_vscode_ext_codelens(sql_file)
    assert result[5].name == "select"
    # assert "SELECT get_total_sales(5)" in result[5].code
    assert result[5].start_line == 44
    assert result[5].end_line == 44


def test_nested_sql_statements(tmp_path):
    # Create a file with nested SQL statements
    d = tmp_path / "nested"
    d.mkdir()
    p = d / "nested.sql"
    p.write_text("SELECT * FROM (SELECT id FROM table);")

    # Test the function
    result = handler.extract_vscode_ext_codelens(p)

    assert len(result) == 1
    assert result[0] == VSCodeExtCodeLensCode(
        name="select",
        # code="SELECT * FROM (SELECT id FROM table)",
        start_line=0,
        end_line=0,
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
    result = handler.extract_vscode_ext_codelens(p)

    assert len(result) == 2
    assert result[0] == VSCodeExtCodeLensCode(
        name="select",
        # code="SELECT * FROM table",
        start_line=0,
        end_line=0,
    )
    assert result[1] == VSCodeExtCodeLensCode(
        name="insert",
        # code="INSERT INTO table VALUES (1, 2, 3)",
        start_line=1,
        end_line=1,
    )


def test_incorrect_sql_syntax(tmp_path):
    # Create a file with incorrect SQL syntax
    d = tmp_path / "incorrect"
    d.mkdir()
    p = d / "incorrect.py"
    p.write_text("SELECT FROM table;")

    # Test the function
    result = handler.extract_vscode_ext_codelens(p)

    assert len(result) == 1
    assert result[0] == VSCodeExtCodeLensCode(
        name="select",
        # code="SELECT FROM table",
        start_line=0,
        end_line=0,
    )
