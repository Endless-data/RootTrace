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
SIMULATED_ADMIN_ID = 1
SIMULATED_ADMIN_USERNAME = "sim_admin"
SURNAMES = ["陈", "李", "王", "张", "刘", "黄", "赵", "吴", "周", "徐"]
MALE_GIVEN_NAMES = [
    "德明",
    "志远",
    "建国",
    "国强",
    "文华",
    "家兴",
    "永康",
    "世杰",
    "俊峰",
    "嘉诚",
    "浩然",
    "子轩",
]
FEMALE_GIVEN_NAMES = [
    "淑兰",
    "秀英",
    "桂芳",
    "玉梅",
    "丽华",
    "美珍",
    "晓燕",
    "静怡",
    "佳慧",
    "思琪",
    "雨桐",
    "若琳",
]
BRANCH_PLACES = ["江苏常州", "浙江绍兴", "福建泉州", "广东佛山", "山东曲阜", "河南洛阳"]
OCCUPATIONS = ["务农", "经商", "从教", "行医", "从军", "做手工营生", "在本地任职", "外出求学"]
BIO_TEMPLATES = [
    "生于{place}，排行第{rank}，成年后主要{occupation}。",
    "族谱记载其为第{generation}代成员，曾居{place}，以{occupation}为业。",
    "早年随家族迁居{place}，在同辈中排行第{rank}，长期{occupation}。",
]

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
    weights = list(range(1, generation_count + 1))
    total_weight = sum(weights)
    allocations = []
    for index, weight in enumerate(weights):
        exact = remaining * weight / total_weight
        whole = int(exact)
        sizes[index] += whole
        allocations.append((exact - whole, index))

    leftover = total - sum(sizes)
    for _, index in sorted(allocations, reverse=True)[:leftover]:
        sizes[index] += 1
    return sizes


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def generation_birth_year(generation, rng):
    return 1248 + (generation - 1) * 26 + rng.randint(0, 2)


def given_name(gender, generation, index, rng):
    names = MALE_GIVEN_NAMES if gender == "male" else FEMALE_GIVEN_NAMES
    return names[(generation + index) % len(names)]


def member_biography(generation, rank, rng):
    return rng.choice(BIO_TEMPLATES).format(
        place=rng.choice(BRANCH_PLACES),
        rank=rank,
        generation=generation,
        occupation=rng.choice(OCCUPATIONS),
    )


def death_year_for(birth_year, rng):
    if birth_year >= 1965:
        return ""
    death_year = birth_year + rng.randint(58, 92)
    return death_year if death_year <= 2026 else ""


def pair_generation_members(member_ids, member_genders):
    males = [member_id for member_id in member_ids if member_genders[member_id] == "male"]
    females = [member_id for member_id in member_ids if member_genders[member_id] == "female"]
    return list(zip(males, females))


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

    users.append(
        {
            "id": SIMULATED_ADMIN_ID,
            "username": SIMULATED_ADMIN_USERNAME,
            "password_hash": SIMULATED_USER_PASSWORD_HASH,
            "display_name": "模拟管理员",
            "created_at": CREATED_AT,
        }
    )

    for tree_id, count in enumerate(counts, start=1):
        surname = SURNAMES[(tree_id - 1) % len(SURNAMES)]
        users.append(
            {
                "id": tree_id + 1,
                "username": f"sim_user_{tree_id}",
                "password_hash": SIMULATED_USER_PASSWORD_HASH,
                "display_name": f"模拟用户 {tree_id}",
                "created_at": CREATED_AT,
            }
        )
        family_trees.append(
            {
                "id": tree_id,
                "name": f"{surname}氏族谱 {tree_id}",
                "surname": surname,
                "revision_time": "2026-05-16",
                "created_by_user_id": SIMULATED_ADMIN_ID,
                "created_at": CREATED_AT,
            }
        )

        generation_count = min(generations, count)
        sizes = generation_sizes(count, generation_count)
        previous_generation_ids = []
        previous_generation_couples = []
        first_member_id = member_id
        tree_relationships = 0
        tree_marriages = 0
        member_genders = {}
        member_birth_years = {}

        for generation, size in enumerate(sizes, start=1):
            current_generation_ids = []
            birth_base = generation_birth_year(generation, rng)
            for index in range(size):
                gender = "male" if index % 2 == 0 else "female"
                birth_year = birth_base + rng.randint(0, 3)
                rank = index + 1
                members.append(
                    {
                        "id": member_id,
                        "family_tree_id": tree_id,
                        "name": f"{surname}{given_name(gender, generation, index, rng)}",
                        "gender": gender,
                        "birth_year": birth_year,
                        "death_year": death_year_for(birth_year, rng),
                        "generation": generation,
                        "biography": member_biography(generation, rank, rng),
                        "created_at": CREATED_AT,
                    }
                )
                current_generation_ids.append(member_id)
                member_genders[member_id] = gender
                member_birth_years[member_id] = birth_year

                if previous_generation_couples:
                    father_id, mother_id = previous_generation_couples[index % len(previous_generation_couples)]
                    for parent_id, relationship_type in ((father_id, "father"), (mother_id, "mother")):
                        parent_child_relationships.append(
                            {
                                "id": relationship_id,
                                "family_tree_id": tree_id,
                                "parent_id": parent_id,
                                "child_id": member_id,
                                "relationship_type": relationship_type,
                            }
                        )
                        relationship_id += 1
                        tree_relationships += 1
                elif previous_generation_ids:
                    parent_id = previous_generation_ids[index % len(previous_generation_ids)]
                    relationship_type = "father" if member_genders[parent_id] == "male" else "mother"
                    parent_child_relationships.append(
                        {
                            "id": relationship_id,
                            "family_tree_id": tree_id,
                            "parent_id": parent_id,
                            "child_id": member_id,
                            "relationship_type": relationship_type,
                        }
                    )
                    relationship_id += 1
                    tree_relationships += 1

                member_id += 1

            current_generation_couples = pair_generation_members(current_generation_ids, member_genders)
            for offset, (person_a_id, person_b_id) in enumerate(current_generation_couples):
                start_year = max(member_birth_years[person_a_id], member_birth_years[person_b_id]) + rng.randint(20, 28)
                end_year = ""
                if start_year < 1950 and offset % 11 == 0:
                    end_year = start_year + rng.randint(18, 45)
                marriages.append(
                    {
                        "id": marriage_id,
                        "family_tree_id": tree_id,
                        "person_a_id": person_a_id,
                        "person_b_id": person_b_id,
                        "start_year": start_year,
                        "end_year": end_year,
                    }
                )
                marriage_id += 1
                tree_marriages += 1

            previous_generation_ids = current_generation_ids
            previous_generation_couples = current_generation_couples

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
