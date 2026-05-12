from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
    )
    username = db.Column(db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    display_name = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    created_family_trees = db.relationship(
        "FamilyTree",
        back_populates="creator",
        cascade="all, delete-orphan",
    )
    family_tree_collaborations = db.relationship(
        "FamilyTreeCollaborator",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class FamilyTree(db.Model):
    __tablename__ = "family_trees"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
    )
    name = db.Column(db.Text, nullable=False)
    surname = db.Column(db.Text, nullable=False)
    revision_time = db.Column(db.Date)
    created_by_user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id"),
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    creator = db.relationship("User", back_populates="created_family_trees")
    collaborators = db.relationship(
        "FamilyTreeCollaborator",
        back_populates="family_tree",
        cascade="all, delete-orphan",
    )
    members = db.relationship(
        "Member",
        back_populates="family_tree",
        cascade="all, delete-orphan",
    )


class FamilyTreeCollaborator(db.Model):
    __tablename__ = "family_tree_collaborators"
    __table_args__ = (
        db.UniqueConstraint(
            "family_tree_id",
            "user_id",
            name="uq_family_tree_collaborators_tree_user",
        ),
    )

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
    )
    family_tree_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("family_trees.id"),
        nullable=False,
    )
    user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("users.id"),
        nullable=False,
    )
    role = db.Column(db.Text, nullable=False, default="editor")
    invited_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    family_tree = db.relationship("FamilyTree", back_populates="collaborators")
    user = db.relationship("User", back_populates="family_tree_collaborations")


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
    )
    family_tree_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("family_trees.id"),
        nullable=False,
    )
    name = db.Column(db.Text, nullable=False)
    gender = db.Column(db.Text, nullable=False, default="unknown")
    birth_year = db.Column(db.Integer)
    death_year = db.Column(db.Integer)
    generation = db.Column(db.Integer)
    biography = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    family_tree = db.relationship("FamilyTree", back_populates="members")
