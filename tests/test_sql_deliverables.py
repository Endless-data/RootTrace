from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "sql" / "queries" / "required_queries.sql"
DOC_PATH = ROOT / "docs" / "sql-queries.md"


def read_sql():
    return SQL_PATH.read_text(encoding="utf-8")


def test_required_sql_file_exists():
    assert SQL_PATH.exists()


def test_required_sql_contains_five_query_sections():
    sql = read_sql()

    for number in range(1, 6):
        assert f"Query {number}:" in sql


def test_required_sql_uses_recursive_cte_for_ancestor_query():
    sql = read_sql().lower()

    assert "with recursive ancestors as" in sql


def test_required_sql_covers_experiment_tables():
    sql = read_sql().lower()

    assert "members" in sql
    assert "marriages" in sql
    assert "parent_child_relationships" in sql


def test_required_sql_uses_psql_input_variables():
    sql = read_sql()

    assert ":member_id" in sql
    assert ":family_tree_id" in sql
    assert "\\set member_id" in sql
    assert "\\set family_tree_id" in sql


def test_required_sql_documents_each_experiment_query():
    document = DOC_PATH.read_text(encoding="utf-8")

    assert "配偶及所有子女" in document
    assert "递归祖先查询" in document
    assert "平均寿命最长的一代" in document
    assert "超过 50 岁且无配偶" in document
    assert "早于同辈平均出生年份" in document
