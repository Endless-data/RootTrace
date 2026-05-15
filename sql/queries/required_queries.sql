-- RootTrace Milestone 11 required SQL deliverables.
-- Target RDBMS: PostgreSQL.
-- The default psql variables allow this file to run against an empty schema.

\set member_id 1
\set family_tree_id 1

-- Query 1: given one member ID, find spouses and all children.
SELECT
    'spouse' AS relationship_kind,
    spouse.id AS related_member_id,
    spouse.name AS related_member_name,
    spouse.gender AS related_member_gender,
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

UNION ALL

SELECT
    'child' AS relationship_kind,
    child.id AS related_member_id,
    child.name AS related_member_name,
    child.gender AS related_member_gender,
    NULL::INTEGER AS start_year,
    NULL::INTEGER AS end_year
FROM members AS base_member
JOIN parent_child_relationships AS relationship
    ON relationship.family_tree_id = base_member.family_tree_id
    AND relationship.parent_id = base_member.id
JOIN members AS child
    ON child.id = relationship.child_id
WHERE base_member.id = :member_id
ORDER BY relationship_kind, related_member_id;

-- Query 2: given one member ID, recursively find all ancestors.
WITH RECURSIVE ancestors AS (
    SELECT
        child.id AS source_member_id,
        parent.id AS ancestor_member_id,
        parent.name AS ancestor_name,
        parent.gender AS ancestor_gender,
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
        parent.id AS ancestor_member_id,
        parent.name AS ancestor_name,
        parent.gender AS ancestor_gender,
        relationship.relationship_type,
        ancestors.depth + 1 AS depth
    FROM ancestors
    JOIN parent_child_relationships AS relationship
        ON relationship.child_id = ancestors.ancestor_member_id
    JOIN members AS parent
        ON parent.id = relationship.parent_id
    WHERE ancestors.depth < 100
)
SELECT
    source_member_id,
    ancestor_member_id,
    ancestor_name,
    ancestor_gender,
    relationship_type,
    depth
FROM ancestors
ORDER BY depth, ancestor_member_id;

-- Query 3: given one family tree ID, find the generation with the longest average lifespan.
SELECT
    family_tree_id,
    generation,
    AVG(COALESCE(death_year, EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER) - birth_year)
        AS average_lifespan_years,
    COUNT(*) AS member_count
FROM members
WHERE family_tree_id = :family_tree_id
    AND generation IS NOT NULL
    AND birth_year IS NOT NULL
GROUP BY family_tree_id, generation
ORDER BY average_lifespan_years DESC, generation
LIMIT 1;

-- Query 4: find male members older than 50 years old and without a spouse.
SELECT
    member.id,
    member.family_tree_id,
    member.name,
    member.birth_year,
    EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER - member.birth_year AS age_years
FROM members AS member
WHERE member.gender = 'male'
    AND member.birth_year IS NOT NULL
    AND EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER - member.birth_year > 50
    AND NOT EXISTS (
        SELECT 1
        FROM marriages AS marriage
        WHERE marriage.family_tree_id = member.family_tree_id
            AND (
                marriage.person_a_id = member.id
                OR marriage.person_b_id = member.id
            )
    )
ORDER BY member.family_tree_id, member.id;

-- Query 5: given one family tree ID, find members born earlier than their generation average.
WITH generation_birth_averages AS (
    SELECT
        family_tree_id,
        generation,
        AVG(birth_year) AS average_birth_year
    FROM members
    WHERE family_tree_id = :family_tree_id
        AND generation IS NOT NULL
        AND birth_year IS NOT NULL
    GROUP BY family_tree_id, generation
)
SELECT
    member.id,
    member.family_tree_id,
    member.name,
    member.generation,
    member.birth_year,
    generation_birth_averages.average_birth_year
FROM members AS member
JOIN generation_birth_averages
    ON generation_birth_averages.family_tree_id = member.family_tree_id
    AND generation_birth_averages.generation = member.generation
WHERE member.birth_year < generation_birth_averages.average_birth_year
ORDER BY member.generation, member.birth_year, member.id;
