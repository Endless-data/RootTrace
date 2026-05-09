# RootTrace Database Design

This document defines the conceptual and logical database design for the RootTrace genealogy management system. The target RDBMS is PostgreSQL.

Milestone 3 only covers database design and DDL validation. It does not implement registration, login, application services, SQLAlchemy models, migrations, or business routes.

## Entities

### users

Stores registered users.

Attributes:
- `id`: primary key.
- `username`: login name, unique.
- `password_hash`: hashed password value for future authentication work.
- `display_name`: user-facing name.
- `created_at`: creation timestamp.

### family_trees

Stores one genealogy tree per family.

Attributes:
- `id`: primary key.
- `name`: genealogy book or tree name.
- `surname`: family surname.
- `revision_time`: genealogy revision date.
- `created_by_user_id`: creator user.
- `created_at`: creation timestamp.

### family_tree_collaborators

Stores invited users who can participate in editing a family tree.

Attributes:
- `id`: primary key.
- `family_tree_id`: family tree.
- `user_id`: invited user.
- `role`: collaborator role.
- `invited_at`: invitation timestamp.

### members

Stores family members inside a family tree.

Attributes:
- `id`: primary key.
- `family_tree_id`: owning family tree.
- `name`: member name.
- `gender`: `male`, `female`, or `unknown`.
- `birth_year`: birth year.
- `death_year`: death year.
- `generation`: generation number inside the family tree.
- `biography`: life summary.
- `created_at`: creation timestamp.

Names are not unique because the experiment explicitly includes people with the same name in different generations. Member identity is always based on `id`.

### parent_child_relationships

Stores blood relationships between two members.

Attributes:
- `id`: primary key.
- `family_tree_id`: owning family tree.
- `parent_id`: parent member.
- `child_id`: child member.
- `relationship_type`: `father` or `mother`.

### marriages

Stores marriage relationships between two members.

Attributes:
- `id`: primary key.
- `family_tree_id`: owning family tree.
- `person_a_id`: one spouse.
- `person_b_id`: the other spouse.
- `start_year`: marriage start year.
- `end_year`: marriage end year.

## Relationships

- One `users` row creates many `family_trees` rows.
- One `family_trees` row has many `members` rows.
- `users` and `family_trees` have a many-to-many collaborator relationship through `family_tree_collaborators`.
- `members` has a recursive many-to-many parent-child relationship through `parent_child_relationships`.
- `members` has a recursive many-to-many marriage relationship through `marriages`.

## Relational Schema

```text
users(id PK, username UNIQUE, password_hash, display_name, created_at)

family_trees(
  id PK,
  name,
  surname,
  revision_time,
  created_by_user_id FK -> users.id,
  created_at
)

family_tree_collaborators(
  id PK,
  family_tree_id FK -> family_trees.id,
  user_id FK -> users.id,
  role,
  invited_at,
  UNIQUE(family_tree_id, user_id)
)

members(
  id PK,
  family_tree_id FK -> family_trees.id,
  name,
  gender,
  birth_year,
  death_year,
  generation,
  biography,
  created_at
)

parent_child_relationships(
  id PK,
  family_tree_id FK -> family_trees.id,
  parent_id FK -> members.id,
  child_id FK -> members.id,
  relationship_type,
  UNIQUE(parent_id, child_id, relationship_type)
)

marriages(
  id PK,
  family_tree_id FK -> family_trees.id,
  person_a_id FK -> members.id,
  person_b_id FK -> members.id,
  start_year,
  end_year,
  person_low_id,
  person_high_id,
  UNIQUE(person_low_id, person_high_id)
)
```

## Constraints

- Every table has a primary key.
- Foreign keys keep users, family trees, members, parent-child relationships, and marriages connected.
- `users.username` is unique.
- `family_tree_collaborators` prevents duplicate collaborator rows for the same user and family tree.
- `members.gender` is checked against `male`, `female`, and `unknown`.
- `members.death_year` must be greater than or equal to `birth_year` when both are present.
- `parent_child_relationships.relationship_type` is checked against `father` and `mother`.
- `parent_child_relationships` prevents a member from being their own parent.
- `marriages` prevents a member from marrying themselves and prevents duplicate A-B/B-A marriage rows by generated ordered IDs.

PostgreSQL `CHECK` constraints cannot compare values from other tables. Therefore, rules such as "a parent birth year must be earlier than a child birth year" will be implemented in a later milestone with a trigger or application-level validation.

## Normalization Analysis

The design targets 3NF.

- Each table represents one entity or relationship type.
- Non-key attributes depend on the whole primary key of their own table.
- Repeating many-to-many data is separated into relationship tables.
- User data is not duplicated in family trees or collaborators.
- Family tree data is not duplicated in members.
- Member names are stored in `members`, while relationship tables store member IDs only.
- Transitive dependencies are avoided: for example, collaborator role belongs to the user-tree relationship, not to `users` or `family_trees`.

BCNF is also largely satisfied for the current design because determinant constraints are represented as keys or unique constraints. Later application rules may introduce additional dependencies and should be rechecked when implemented.

## Notes For Later Milestones

- Authentication behavior belongs to Milestone 4.
- SQLAlchemy models and migrations are not part of Milestone 3.
- Query SQL, indexes, import/export, and performance experiments are separate later milestones.
