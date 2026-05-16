-- RootTrace Milestone 14 index strategy.
-- Target RDBMS: PostgreSQL 16.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_members_name_trgm
    ON members USING gin (name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_members_family_tree
    ON members (family_tree_id);

CREATE INDEX IF NOT EXISTS idx_members_family_tree_generation
    ON members (family_tree_id, generation);

CREATE INDEX IF NOT EXISTS idx_members_family_tree_gender_birth
    ON members (family_tree_id, gender, birth_year);

CREATE INDEX IF NOT EXISTS idx_parent_child_family_tree_parent
    ON parent_child_relationships (family_tree_id, parent_id);

CREATE INDEX IF NOT EXISTS idx_parent_child_family_tree_child
    ON parent_child_relationships (family_tree_id, child_id);

CREATE INDEX IF NOT EXISTS idx_marriages_family_tree_person_a
    ON marriages (family_tree_id, person_a_id);

CREATE INDEX IF NOT EXISTS idx_marriages_family_tree_person_b
    ON marriages (family_tree_id, person_b_id);
