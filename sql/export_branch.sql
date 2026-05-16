\set root_member_id 1
\set output_path '/exports/branch_export.csv'

COPY (
    WITH RECURSIVE branch_members AS (
        SELECT
            member.id,
            member.family_tree_id,
            member.name,
            member.gender,
            member.birth_year,
            member.death_year,
            member.generation,
            0 AS depth
        FROM members AS member
        WHERE member.id = :root_member_id

        UNION ALL

        SELECT
            child.id,
            child.family_tree_id,
            child.name,
            child.gender,
            child.birth_year,
            child.death_year,
            child.generation,
            branch_members.depth + 1 AS depth
        FROM branch_members
        JOIN parent_child_relationships AS relationship
            ON relationship.parent_id = branch_members.id
        JOIN members AS child
            ON child.id = relationship.child_id
        WHERE branch_members.depth < 100
    )
    SELECT
        id,
        family_tree_id,
        name,
        gender,
        birth_year,
        death_year,
        generation,
        depth
    FROM branch_members
    ORDER BY depth, generation, id
) TO :'output_path'
WITH (FORMAT csv, HEADER true);
