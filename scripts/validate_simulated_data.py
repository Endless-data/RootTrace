import argparse
import csv
import json
from pathlib import Path


EXPECTED_COLUMNS = {
    "users.csv": ["id", "username", "password_hash", "display_name", "created_at"],
    "family_trees.csv": [
        "id",
        "name",
        "surname",
        "revision_time",
        "created_by_user_id",
        "created_at",
    ],
    "members.csv": [
        "id",
        "family_tree_id",
        "name",
        "gender",
        "birth_year",
        "death_year",
        "generation",
        "biography",
        "created_at",
    ],
    "parent_child_relationships.csv": [
        "id",
        "family_tree_id",
        "parent_id",
        "child_id",
        "relationship_type",
    ],
    "marriages.csv": ["id", "family_tree_id", "person_a_id", "person_b_id", "start_year", "end_year"],
}

SIMULATED_ADMIN_ID = 1
SIMULATED_ADMIN_USERNAME = "sim_admin"


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != EXPECTED_COLUMNS[path.name]:
            raise ValueError(f"{path.name} columns do not match expected schema")
        return list(reader)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(output_dir, require_full=True):
    output_dir = Path(output_dir)
    rows = {}
    for filename in EXPECTED_COLUMNS:
        path = output_dir / filename
        require(path.exists(), f"missing {filename}")
        rows[filename] = read_rows(path)

    manifest_path = output_dir / "manifest.json"
    require(manifest_path.exists(), "missing manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    user_ids = {int(row["id"]) for row in rows["users.csv"]}
    require(len(user_ids) == len(rows["users.csv"]), "duplicate user id")
    admin_rows = [
        row
        for row in rows["users.csv"]
        if int(row["id"]) == SIMULATED_ADMIN_ID and row["username"] == SIMULATED_ADMIN_USERNAME
    ]
    require(len(admin_rows) == 1, "missing simulated admin user")

    tree_ids = {int(row["id"]) for row in rows["family_trees.csv"]}
    require(len(tree_ids) == len(rows["family_trees.csv"]), "duplicate family tree id")
    for row in rows["family_trees.csv"]:
        creator_id = int(row["created_by_user_id"])
        require(creator_id in user_ids, f"family tree {row['id']} references unknown creator")
        require(creator_id == SIMULATED_ADMIN_ID, f"family tree {row['id']} is not owned by simulated admin")

    member_tree = {}
    member_birth_year = {}
    member_generation = {}
    per_tree_members = {tree_id: 0 for tree_id in tree_ids}
    per_tree_generations = {tree_id: set() for tree_id in tree_ids}
    for row in rows["members.csv"]:
        member_id = int(row["id"])
        tree_id = int(row["family_tree_id"])
        require(tree_id in tree_ids, f"member {member_id} references unknown family tree")
        require(row["gender"] in {"male", "female", "unknown"}, f"member {member_id} has invalid gender")
        require(row["birth_year"], f"member {member_id} is missing birth year")
        require(row["generation"], f"member {member_id} is missing generation")
        member_tree[member_id] = tree_id
        member_birth_year[member_id] = int(row["birth_year"])
        member_generation[member_id] = int(row["generation"])
        per_tree_members[tree_id] += 1
        per_tree_generations[tree_id].add(int(row["generation"]))
        if row["death_year"]:
            require(int(row["death_year"]) >= int(row["birth_year"]), f"member {member_id} dies before birth")

    per_tree_relationships = {tree_id: 0 for tree_id in tree_ids}
    relationship_pairs = set()
    for row in rows["parent_child_relationships.csv"]:
        parent_id = int(row["parent_id"])
        child_id = int(row["child_id"])
        tree_id = int(row["family_tree_id"])
        require(parent_id in member_tree, f"relationship references unknown parent {parent_id}")
        require(child_id in member_tree, f"relationship references unknown child {child_id}")
        require(parent_id != child_id, "parent-child relationship points to same member")
        require(member_tree[parent_id] == tree_id, "parent belongs to a different family tree")
        require(member_tree[child_id] == tree_id, "child belongs to a different family tree")
        require(member_birth_year[parent_id] < member_birth_year[child_id], "parent is not older than child")
        require(row["relationship_type"] in {"father", "mother"}, "invalid relationship type")
        pair = (parent_id, child_id, row["relationship_type"])
        require(pair not in relationship_pairs, "duplicate parent-child relationship")
        relationship_pairs.add(pair)
        per_tree_relationships[tree_id] += 1

    marriage_pairs = set()
    for row in rows["marriages.csv"]:
        person_a_id = int(row["person_a_id"])
        person_b_id = int(row["person_b_id"])
        tree_id = int(row["family_tree_id"])
        require(person_a_id in member_tree, f"marriage references unknown member {person_a_id}")
        require(person_b_id in member_tree, f"marriage references unknown member {person_b_id}")
        require(person_a_id != person_b_id, "marriage points to same member")
        require(member_tree[person_a_id] == tree_id, "marriage member A belongs to a different family tree")
        require(member_tree[person_b_id] == tree_id, "marriage member B belongs to a different family tree")
        pair = tuple(sorted((person_a_id, person_b_id)))
        require(pair not in marriage_pairs, "duplicate marriage pair")
        marriage_pairs.add(pair)

    require(all(count > 0 for count in per_tree_relationships.values()), "a family tree has no relationships")

    summary = {
        "family_tree_count": len(tree_ids),
        "member_count": len(member_tree),
        "largest_family_tree_member_count": max(per_tree_members.values()),
        "max_generation_count": max(len(generations) for generations in per_tree_generations.values()),
        "parent_child_relationship_count": len(rows["parent_child_relationships.csv"]),
        "marriage_count": len(rows["marriages.csv"]),
    }
    for key, value in summary.items():
        require(manifest.get(key) == value, f"manifest {key} does not match generated data")

    if require_full:
        require(summary["family_tree_count"] >= 10, "fewer than 10 family trees")
        require(summary["member_count"] >= 100000, "fewer than 100000 members")
        require(summary["largest_family_tree_member_count"] > 50000, "no family tree has more than 50000 members")
        require(summary["max_generation_count"] >= 30, "no family tree has at least 30 generations")

    return summary


def parse_args():
    parser = argparse.ArgumentParser(description="Validate RootTrace simulated genealogy CSV data.")
    parser.add_argument("output", help="Generated data directory.")
    parser.add_argument("--allow-small", action="store_true", help="Skip full experiment scale checks.")
    return parser.parse_args()


def main():
    args = parse_args()
    summary = validate(args.output, require_full=not args.allow_small)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
