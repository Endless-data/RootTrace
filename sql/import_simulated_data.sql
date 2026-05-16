COPY users (
    id,
    username,
    password_hash,
    display_name,
    created_at
)
FROM '/generated/users.csv'
WITH (FORMAT csv, HEADER true);

COPY family_trees (
    id,
    name,
    surname,
    revision_time,
    created_by_user_id,
    created_at
)
FROM '/generated/family_trees.csv'
WITH (FORMAT csv, HEADER true);

COPY members (
    id,
    family_tree_id,
    name,
    gender,
    birth_year,
    death_year,
    generation,
    biography,
    created_at
)
FROM '/generated/members.csv'
WITH (FORMAT csv, HEADER true);

COPY parent_child_relationships (
    id,
    family_tree_id,
    parent_id,
    child_id,
    relationship_type
)
FROM '/generated/parent_child_relationships.csv'
WITH (FORMAT csv, HEADER true);

COPY marriages (
    id,
    family_tree_id,
    person_a_id,
    person_b_id,
    start_year,
    end_year
)
FROM '/generated/marriages.csv'
WITH (FORMAT csv, HEADER true);

SELECT setval(
    pg_get_serial_sequence('users', 'id'),
    COALESCE((SELECT MAX(id) FROM users), 1),
    (SELECT COUNT(*) > 0 FROM users)
);
SELECT setval(
    pg_get_serial_sequence('family_trees', 'id'),
    COALESCE((SELECT MAX(id) FROM family_trees), 1),
    (SELECT COUNT(*) > 0 FROM family_trees)
);
SELECT setval(
    pg_get_serial_sequence('members', 'id'),
    COALESCE((SELECT MAX(id) FROM members), 1),
    (SELECT COUNT(*) > 0 FROM members)
);
SELECT setval(
    pg_get_serial_sequence('parent_child_relationships', 'id'),
    COALESCE((SELECT MAX(id) FROM parent_child_relationships), 1),
    (SELECT COUNT(*) > 0 FROM parent_child_relationships)
);
SELECT setval(
    pg_get_serial_sequence('marriages', 'id'),
    COALESCE((SELECT MAX(id) FROM marriages), 1),
    (SELECT COUNT(*) > 0 FROM marriages)
);
