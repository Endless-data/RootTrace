from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_database_design_artifacts_exist():
    assert (ROOT / "docs/database-design.md").is_file()
    assert (ROOT / "docs/er.mmd").is_file()
    assert (ROOT / "sql/schema.sql").is_file()
    assert (ROOT / "compose.yaml").is_file()


def test_schema_defines_core_tables_and_constraints():
    schema = read_text("sql/schema.sql")

    for table_name in (
        "users",
        "family_trees",
        "family_tree_collaborators",
        "members",
        "parent_child_relationships",
        "marriages",
    ):
        assert f"CREATE TABLE {table_name}" in schema

    for keyword in ("PRIMARY KEY", "REFERENCES", "UNIQUE", "CHECK"):
        assert keyword in schema


def test_design_document_covers_required_topics():
    design = read_text("docs/database-design.md")

    for phrase in (
        "PostgreSQL",
        "3NF",
        "Relationships",
        "Relational Schema",
        "Constraints",
        "parent birth year",
    ):
        assert phrase in design


def test_er_diagram_contains_core_entities():
    er_diagram = read_text("docs/er.mmd")

    for entity in (
        "USERS",
        "FAMILY_TREES",
        "FAMILY_TREE_COLLABORATORS",
        "MEMBERS",
        "PARENT_CHILD_RELATIONSHIPS",
        "MARRIAGES",
    ):
        assert entity in er_diagram
