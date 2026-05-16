import argparse
import csv
import json
import random
from pathlib import Path


CREATED_AT = "2026-05-16T00:00:00+08:00"
SIMULATED_USER_PASSWORD = "roottrace-demo"
SIMULATED_USER_PASSWORD_HASH = (
    "pbkdf2:sha256:1000000$k2KBcI6O67YCMZTO$"
    "3700e5102982126cf1e0b664b31007f83fe93ab5b30517b1636fba4740d99e11"
)
SURNAMES = ["Chen", "Li", "Wang", "Zhang", "Liu", "Huang", "Zhao", "Wu", "Zhou", "Xu"]

CSV_COLUMNS = {
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


def member_counts(tree_count, total_members, large_tree_members):
    if tree_count < 1:
        raise ValueError("tree_count must be positive")
    if total_members < large_tree_members:
        raise ValueError("total_members must be greater than or equal to large_tree_members")
    if tree_count == 1:
        return [total_members]

    remaining = total_members - large_tree_members
    base = remaining // (tree_count - 1)
    extra = remaining % (tree_count - 1)
    return [large_tree_members] + [base + (1 if index < extra else 0) for index in range(tree_count - 1)]


def generation_sizes(total, generation_count):
    sizes = [1] * generation_count
    remaining = total - generation_count
    index = 0
    while remaining > 0:
        sizes[index % generation_count] += 1
        remaining -= 1
        index += 1
    return sizes


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def generate_data(output_dir, seed, tree_count, total_members, large_tree_members, generations):
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    counts = member_counts(tree_count, total_members, large_tree_members)

    users = []
    family_trees = []
    members = []
    parent_child_relationships = []
    marriages = []
    per_tree_stats = []
    member_id = 1
    relationship_id = 1
    marriage_id = 1

    for tree_id, count in enumerate(counts, start=1):
        surname = SURNAMES[(tree_id - 1) % len(SURNAMES)]
        users.append(
            {
                "id": tree_id,
                "username": f"sim_user_{tree_id}",
                "password_hash": SIMULATED_USER_PASSWORD_HASH,
                "display_name": f"Simulated User {tree_id}",
                "created_at": CREATED_AT,
            }
        )
        family_trees.append(
            {
                "id": tree_id,
                "name": f"{surname} Genealogy {tree_id}",
                "surname": surname,
                "revision_time": "2026-05-16",
                "created_by_user_id": tree_id,
                "created_at": CREATED_AT,
            }
        )

        generation_count = min(generations, count)
        sizes = generation_sizes(count, generation_count)
        previous_generation_ids = []
        first_member_id = member_id
        tree_relationships = 0
        tree_marriages = 0
        tree_generation_ids = []

        for generation, size in enumerate(sizes, start=1):
            current_generation_ids = []
            birth_base = 1900 + (generation - 1) * 3
            for index in range(size):
                gender = "male" if (member_id + generation + index) % 2 == 0 else "female"
                birth_year = birth_base + rng.randint(0, 2)
                death_year = ""
                if birth_year <= 1955:
                    death_year = birth_year + rng.randint(55, 88)
                members.append(
                    {
                        "id": member_id,
                        "family_tree_id": tree_id,
                        "name": f"{surname} Member {member_id}",
                        "gender": gender,
                        "birth_year": birth_year,
                        "death_year": death_year,
                        "generation": generation,
                        "biography": f"Simulated member in generation {generation}.",
                        "created_at": CREATED_AT,
                    }
                )
                current_generation_ids.append(member_id)

                if previous_generation_ids:
                    parent_id = previous_generation_ids[index % len(previous_generation_ids)]
                    parent_child_relationships.append(
                        {
                            "id": relationship_id,
                            "family_tree_id": tree_id,
                            "parent_id": parent_id,
                            "child_id": member_id,
                            "relationship_type": "father" if parent_id % 2 == 0 else "mother",
                        }
                    )
                    relationship_id += 1
                    tree_relationships += 1

                member_id += 1

            tree_generation_ids.append(current_generation_ids)
            previous_generation_ids = current_generation_ids

        for ids in tree_generation_ids:
            pair_limit = min(len(ids) // 2, max(1, len(ids) // 20))
            for offset in range(pair_limit):
                person_a_id = ids[offset * 2]
                person_b_id = ids[offset * 2 + 1]
                marriages.append(
                    {
                        "id": marriage_id,
                        "family_tree_id": tree_id,
                        "person_a_id": person_a_id,
                        "person_b_id": person_b_id,
                        "start_year": "",
                        "end_year": "",
                    }
                )
                marriage_id += 1
                tree_marriages += 1

        per_tree_stats.append(
            {
                "family_tree_id": tree_id,
                "member_count": count,
                "generation_count": generation_count,
                "parent_child_relationship_count": tree_relationships,
                "marriage_count": tree_marriages,
                "first_member_id": first_member_id,
                "last_member_id": member_id - 1,
            }
        )

    write_csv(output_dir / "users.csv", CSV_COLUMNS["users.csv"], users)
    write_csv(output_dir / "family_trees.csv", CSV_COLUMNS["family_trees.csv"], family_trees)
    write_csv(output_dir / "members.csv", CSV_COLUMNS["members.csv"], members)
    write_csv(
        output_dir / "parent_child_relationships.csv",
        CSV_COLUMNS["parent_child_relationships.csv"],
        parent_child_relationships,
    )
    write_csv(output_dir / "marriages.csv", CSV_COLUMNS["marriages.csv"], marriages)

    manifest = {
        "seed": seed,
        "generated_at": CREATED_AT,
        "family_tree_count": len(family_trees),
        "member_count": len(members),
        "largest_family_tree_member_count": max(item["member_count"] for item in per_tree_stats),
        "max_generation_count": max(item["generation_count"] for item in per_tree_stats),
        "parent_child_relationship_count": len(parent_child_relationships),
        "marriage_count": len(marriages),
        "files": sorted(CSV_COLUMNS),
        "family_trees": per_tree_stats,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def parse_args():
    parser = argparse.ArgumentParser(description="Generate RootTrace simulated genealogy CSV data.")
    parser.add_argument("--output", default="data/generated", help="Output directory for generated files.")
    parser.add_argument("--seed", type=int, default=20260516, help="Random seed for reproducible data.")
    parser.add_argument("--scale", choices=["full", "test"], default="full")
    parser.add_argument("--tree-count", type=int)
    parser.add_argument("--total-members", type=int)
    parser.add_argument("--large-tree-members", type=int)
    parser.add_argument("--generations", type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.scale == "test":
        defaults = {
            "tree_count": 3,
            "total_members": 120,
            "large_tree_members": 60,
            "generations": 6,
        }
    else:
        defaults = {
            "tree_count": 10,
            "total_members": 100000,
            "large_tree_members": 50001,
            "generations": 30,
        }

    manifest = generate_data(
        output_dir=Path(args.output),
        seed=args.seed,
        tree_count=args.tree_count or defaults["tree_count"],
        total_members=args.total_members or defaults["total_members"],
        large_tree_members=args.large_tree_members or defaults["large_tree_members"],
        generations=args.generations or defaults["generations"],
    )
    print(
        "Generated "
        f"{manifest['member_count']} members across {manifest['family_tree_count']} family trees "
        f"into {args.output}"
    )


if __name__ == "__main__":
    main()
