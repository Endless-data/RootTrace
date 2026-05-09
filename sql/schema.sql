DROP TABLE IF EXISTS marriages;
DROP TABLE IF EXISTS parent_child_relationships;
DROP TABLE IF EXISTS members;
DROP TABLE IF EXISTS family_tree_collaborators;
DROP TABLE IF EXISTS family_trees;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE family_trees (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    revision_time DATE,
    created_by_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE family_tree_collaborators (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    family_tree_id BIGINT NOT NULL REFERENCES family_trees(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'editor',
    invited_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_family_tree_collaborators_tree_user UNIQUE (family_tree_id, user_id),
    CONSTRAINT ck_family_tree_collaborators_role CHECK (role IN ('editor'))
);

CREATE TABLE members (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    family_tree_id BIGINT NOT NULL REFERENCES family_trees(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    gender TEXT NOT NULL DEFAULT 'unknown',
    birth_year INTEGER,
    death_year INTEGER,
    generation INTEGER,
    biography TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_members_gender CHECK (gender IN ('male', 'female', 'unknown')),
    CONSTRAINT ck_members_life_years CHECK (
        birth_year IS NULL
        OR death_year IS NULL
        OR death_year >= birth_year
    ),
    CONSTRAINT ck_members_generation CHECK (generation IS NULL OR generation > 0)
);

CREATE TABLE parent_child_relationships (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    family_tree_id BIGINT NOT NULL REFERENCES family_trees(id) ON DELETE CASCADE,
    parent_id BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    child_id BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    CONSTRAINT uq_parent_child_relationships_pair_type UNIQUE (
        parent_id,
        child_id,
        relationship_type
    ),
    CONSTRAINT ck_parent_child_relationships_type CHECK (
        relationship_type IN ('father', 'mother')
    ),
    CONSTRAINT ck_parent_child_relationships_not_self CHECK (parent_id <> child_id)
);

CREATE TABLE marriages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    family_tree_id BIGINT NOT NULL REFERENCES family_trees(id) ON DELETE CASCADE,
    person_a_id BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    person_b_id BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    start_year INTEGER,
    end_year INTEGER,
    person_low_id BIGINT GENERATED ALWAYS AS (LEAST(person_a_id, person_b_id)) STORED,
    person_high_id BIGINT GENERATED ALWAYS AS (GREATEST(person_a_id, person_b_id)) STORED,
    CONSTRAINT uq_marriages_ordered_pair UNIQUE (person_low_id, person_high_id),
    CONSTRAINT ck_marriages_not_self CHECK (person_a_id <> person_b_id),
    CONSTRAINT ck_marriages_years CHECK (
        start_year IS NULL
        OR end_year IS NULL
        OR end_year >= start_year
    )
);
