import csv
import json

from werkzeug.security import check_password_hash

from scripts.generate_simulated_data import SIMULATED_ADMIN_USERNAME, SIMULATED_USER_PASSWORD, generate_data
from scripts.validate_simulated_data import validate


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_generate_simulated_data_creates_expected_files(tmp_path):
    manifest = generate_data(
        output_dir=tmp_path,
        seed=123,
        tree_count=3,
        total_members=120,
        large_tree_members=60,
        generations=6,
    )

    assert manifest["family_tree_count"] == 3
    assert manifest["member_count"] == 120
    assert manifest["largest_family_tree_member_count"] == 60
    assert manifest["max_generation_count"] == 6
    for filename in (
        "users.csv",
        "family_trees.csv",
        "members.csv",
        "parent_child_relationships.csv",
        "marriages.csv",
        "manifest.json",
    ):
        assert (tmp_path / filename).exists()


def test_generated_data_validates_at_small_scale(tmp_path):
    generate_data(
        output_dir=tmp_path,
        seed=123,
        tree_count=3,
        total_members=120,
        large_tree_members=60,
        generations=6,
    )

    summary = validate(tmp_path, require_full=False)

    assert summary["family_tree_count"] == 3
    assert summary["member_count"] == 120
    assert summary["parent_child_relationship_count"] > 0


def test_generated_users_can_login_with_demo_password(tmp_path):
    generate_data(
        output_dir=tmp_path,
        seed=123,
        tree_count=3,
        total_members=120,
        large_tree_members=60,
        generations=6,
    )

    users = read_csv(tmp_path / "users.csv")

    assert users[0]["username"] == SIMULATED_ADMIN_USERNAME
    assert users[0]["display_name"] == "模拟管理员"
    assert users[0]["password_hash"] != SIMULATED_USER_PASSWORD
    assert check_password_hash(users[0]["password_hash"], SIMULATED_USER_PASSWORD)
    assert users[1]["username"] == "sim_user_1"
    assert users[1]["display_name"] == "模拟用户 1"
    assert check_password_hash(users[1]["password_hash"], SIMULATED_USER_PASSWORD)


def test_generated_family_trees_are_owned_by_admin_and_use_chinese_content(tmp_path):
    generate_data(
        output_dir=tmp_path,
        seed=123,
        tree_count=3,
        total_members=120,
        large_tree_members=60,
        generations=6,
    )

    family_trees = read_csv(tmp_path / "family_trees.csv")
    members = read_csv(tmp_path / "members.csv")

    assert {row["created_by_user_id"] for row in family_trees} == {"1"}
    assert family_trees[0]["name"] == "陈氏族谱 1"
    assert family_trees[0]["surname"] == "陈"
    assert members[0]["name"].startswith("陈氏第 1 代成员")
    assert members[0]["biography"] == "第 1 代模拟成员。"


def test_generated_data_is_reproducible_for_same_seed(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    generate_data(first, seed=2026, tree_count=3, total_members=120, large_tree_members=60, generations=6)
    generate_data(second, seed=2026, tree_count=3, total_members=120, large_tree_members=60, generations=6)

    assert (first / "members.csv").read_text(encoding="utf-8") == (
        second / "members.csv"
    ).read_text(encoding="utf-8")
    assert json.loads((first / "manifest.json").read_text(encoding="utf-8")) == json.loads(
        (second / "manifest.json").read_text(encoding="utf-8")
    )


def test_generated_relationships_keep_parents_older_than_children(tmp_path):
    generate_data(
        output_dir=tmp_path,
        seed=123,
        tree_count=3,
        total_members=120,
        large_tree_members=60,
        generations=6,
    )
    members = {int(row["id"]): row for row in read_csv(tmp_path / "members.csv")}
    relationships = read_csv(tmp_path / "parent_child_relationships.csv")

    assert relationships
    for relationship in relationships:
        parent = members[int(relationship["parent_id"])]
        child = members[int(relationship["child_id"])]
        assert int(parent["family_tree_id"]) == int(child["family_tree_id"])
        assert int(parent["birth_year"]) < int(child["birth_year"])
