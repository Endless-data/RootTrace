from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_SQL = ROOT / "sql" / "indexes.sql"
PERFORMANCE_SQL = ROOT / "sql" / "performance_experiment.sql"
PERFORMANCE_DOC = ROOT / "docs" / "performance-analysis.md"


def test_index_sql_defines_required_indexes():
    sql = INDEX_SQL.read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS pg_trgm" in sql
    assert "idx_members_name_trgm" in sql
    assert "USING gin (name gin_trgm_ops)" in sql
    assert "idx_parent_child_family_tree_parent" in sql
    assert "idx_parent_child_family_tree_child" in sql
    assert "idx_marriages_family_tree_person_a" in sql
    assert "idx_marriages_family_tree_person_b" in sql


def test_index_sql_is_idempotent():
    sql = INDEX_SQL.read_text(encoding="utf-8")

    assert "CREATE INDEX IF NOT EXISTS" in sql


def test_performance_experiment_uses_explain_analyze_buffers():
    sql = PERFORMANCE_SQL.read_text(encoding="utf-8")

    assert sql.count("EXPLAIN (ANALYZE, BUFFERS)") >= 3
    assert ":family_tree_id" in sql
    assert ":member_id" in sql
    assert ":parent_id" in sql
    assert "ILIKE '%' || :name_keyword || '%'" in sql
    assert "WITH RECURSIVE ancestors AS" in sql


def test_performance_document_records_strategy_and_commands():
    document = PERFORMANCE_DOC.read_text(encoding="utf-8")

    assert "PostgreSQL" in document
    assert "postgres:16-alpine" in document
    assert "sql/indexes.sql" in document
    assert "sql/performance_experiment.sql" in document
    assert "成员姓名模糊搜索" in document
    assert "按父成员查询子女" in document
    assert "递归祖先查询" in document
    assert "建索引前" in document
    assert "建索引后" in document
