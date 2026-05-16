-- RootTrace Milestone 14 performance experiment.
-- Run once before sql/indexes.sql and once after sql/indexes.sql.

\set family_tree_id 1
\set member_id 50001
\set parent_id 1
\set name_keyword '''RootTrace Member 1'''

\echo 'Experiment 1: fuzzy member name search'
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    family_tree_id,
    name,
    gender,
    birth_year,
    generation
FROM members
WHERE family_tree_id = :family_tree_id
    AND name ILIKE '%' || :name_keyword || '%'
ORDER BY id
LIMIT 20;

\echo 'Experiment 2: children lookup by parent id'
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    child.id,
    child.name,
    child.gender,
    child.birth_year,
    relationship.relationship_type
FROM parent_child_relationships AS relationship
JOIN members AS child
    ON child.id = relationship.child_id
WHERE relationship.family_tree_id = :family_tree_id
    AND relationship.parent_id = :parent_id
ORDER BY child.id;

\echo 'Experiment 3: recursive ancestor lookup'
EXPLAIN (ANALYZE, BUFFERS)
WITH RECURSIVE ancestors AS (
    SELECT
        child.id AS source_member_id,
        child.family_tree_id,
        parent.id AS ancestor_member_id,
        parent.name AS ancestor_name,
        relationship.relationship_type,
        1 AS depth
    FROM members AS child
    JOIN parent_child_relationships AS relationship
        ON relationship.family_tree_id = child.family_tree_id
        AND relationship.child_id = child.id
    JOIN members AS parent
        ON parent.id = relationship.parent_id
    WHERE child.id = :member_id

    UNION ALL

    SELECT
        ancestors.source_member_id,
        ancestors.family_tree_id,
        parent.id AS ancestor_member_id,
        parent.name AS ancestor_name,
        relationship.relationship_type,
        ancestors.depth + 1 AS depth
    FROM ancestors
    JOIN parent_child_relationships AS relationship
        ON relationship.family_tree_id = ancestors.family_tree_id
        AND relationship.child_id = ancestors.ancestor_member_id
    JOIN members AS parent
        ON parent.id = relationship.parent_id
    WHERE ancestors.depth < 100
)
SELECT
    source_member_id,
    ancestor_member_id,
    ancestor_name,
    relationship_type,
    depth
FROM ancestors
ORDER BY depth, ancestor_member_id;

\echo 'Experiment 4: spouse lookup by member id'
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    spouse.id,
    spouse.name,
    spouse.gender,
    marriage.start_year,
    marriage.end_year
FROM members AS base_member
JOIN marriages AS marriage
    ON marriage.family_tree_id = base_member.family_tree_id
    AND (
        marriage.person_a_id = base_member.id
        OR marriage.person_b_id = base_member.id
    )
JOIN members AS spouse
    ON spouse.id = CASE
        WHEN marriage.person_a_id = base_member.id THEN marriage.person_b_id
        ELSE marriage.person_a_id
    END
WHERE base_member.id = :member_id
ORDER BY spouse.id;
