from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPORT_SQL = ROOT / "sql" / "import_simulated_data.sql"
EXPORT_SQL = ROOT / "sql" / "export_branch.sql"
IMPORT_EXPORT_DOC = ROOT / "docs" / "import-export.md"
COMPOSE = ROOT / "compose.yaml"


def test_import_sql_uses_copy_from_for_generated_csv_files():
    sql = IMPORT_SQL.read_text(encoding="utf-8")

    assert "COPY users" in sql
    assert "COPY family_trees" in sql
    assert "COPY members" in sql
    assert "COPY parent_child_relationships" in sql
    assert "COPY marriages" in sql
    assert "FROM '/generated/users.csv'" in sql
    assert "setval" in sql


def test_export_sql_uses_recursive_cte_and_copy_to():
    sql = EXPORT_SQL.read_text(encoding="utf-8")

    assert "\\set root_member_id" in sql
    assert "\\set output_path" in sql
    assert "WITH RECURSIVE branch_members AS" in sql
    assert "COPY (" in sql
    assert "TO :'output_path'" in sql


def test_compose_mounts_generated_data_and_exports():
    compose = COMPOSE.read_text(encoding="utf-8")

    assert "./data/generated:/generated:ro" in compose
    assert "./exports:/exports" in compose


def test_import_export_documentation_records_rdbms_and_commands():
    document = IMPORT_EXPORT_DOC.read_text(encoding="utf-8")

    assert "PostgreSQL" in document
    assert "postgres:16-alpine" in document
    assert "import_simulated_data.sql" in document
    assert "export_branch.sql" in document
    assert "SELECT COUNT(*) FROM members;" in document
