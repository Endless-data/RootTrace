import pytest

from app import create_app
from app.extensions import db
from app.models import FamilyTree, FamilyTreeCollaborator, Member, ParentChildRelationship, User


@pytest.fixture()
def app():
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username, display_name=None, password="secret"):
    return client.post(
        "/auth/register",
        data={
            "username": username,
            "display_name": display_name or username.title(),
            "password": password,
        },
    )


def login(client, username, password="secret"):
    return client.post("/auth/login", data={"username": username, "password": password})


def create_family_tree(client, name="Chen Genealogy", surname="Chen"):
    return client.post(
        "/family-trees/new",
        data={"name": name, "surname": surname, "revision_time": ""},
    )


def create_member(client, tree_id, name, gender="unknown", generation=""):
    return client.post(
        f"/family-trees/{tree_id}/members/new",
        data={
            "name": name,
            "gender": gender,
            "birth_year": "",
            "death_year": "",
            "generation": generation,
            "biography": "",
        },
    )


def setup_tree(app, client):
    register(client, "alice")
    login(client, "alice")
    create_family_tree(client)
    with app.app_context():
        return FamilyTree.query.filter_by(name="Chen Genealogy").one().id


def test_dashboard_stats_show_member_counts_and_ratios(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Father", gender="male")
    create_member(client, tree_id, "Mother", gender="female")
    create_member(client, tree_id, "Unknown", gender="unknown")

    response = client.get(f"/family-trees/{tree_id}")

    assert response.status_code == 200
    assert b"Total members" in response.data
    assert b"3" in response.data
    assert b"33.3%" in response.data


def test_dashboard_handles_empty_family_tree(client, app):
    tree_id = setup_tree(app, client)

    response = client.get(f"/family-trees/{tree_id}")

    assert response.status_code == 200
    assert b"Total members" in response.data
    assert b"0.0%" in response.data


def test_tree_preview_requires_login(client):
    response = client.get("/family-trees/1/tree-preview")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_tree_preview_displays_descendant_branch_with_ids(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Chen Ming", gender="male", generation="1")
    create_member(client, tree_id, "Chen Ming", gender="female", generation="2")
    create_member(client, tree_id, "Grandchild", gender="unknown", generation="3")
    with app.app_context():
        root = Member.query.filter_by(generation=1).one()
        child = Member.query.filter_by(generation=2).one()
        grandchild = Member.query.filter_by(name="Grandchild").one()
        db.session.add(
            ParentChildRelationship(
                family_tree_id=tree_id,
                parent_id=root.id,
                child_id=child.id,
                relationship_type="father",
            )
        )
        db.session.add(
            ParentChildRelationship(
                family_tree_id=tree_id,
                parent_id=child.id,
                child_id=grandchild.id,
                relationship_type="mother",
            )
        )
        db.session.commit()
        root_id = root.id
        child_id = child.id

    response = client.get(f"/family-trees/{tree_id}/tree-preview?root_member_id={root_id}")

    assert response.status_code == 200
    assert b"Descendants of Chen Ming" in response.data
    assert f"#{root_id}".encode() in response.data
    assert f"#{child_id}".encode() in response.data
    assert b"Grandchild" in response.data


def test_tree_preview_shows_no_descendants(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Only Member")
    with app.app_context():
        member_id = Member.query.filter_by(name="Only Member").one().id

    response = client.get(f"/family-trees/{tree_id}/tree-preview?root_member_id={member_id}")

    assert response.status_code == 200
    assert b"No descendants" in response.data


def test_tree_preview_rejects_root_from_other_tree(app, client):
    tree_id = setup_tree(app, client)
    with app.app_context():
        alice = User.query.filter_by(username="alice").one()
        other_tree = FamilyTree(name="Other", surname="Li", created_by_user_id=alice.id)
        db.session.add(other_tree)
        db.session.flush()
        other_member = Member(family_tree_id=other_tree.id, name="Other Root")
        db.session.add(other_member)
        db.session.commit()
        other_member_id = other_member.id

    response = client.get(
        f"/family-trees/{tree_id}/tree-preview?root_member_id={other_member_id}"
    )

    assert response.status_code == 404


def test_uninvited_user_cannot_view_tree_preview(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Root")
    with app.app_context():
        root_id = Member.query.filter_by(name="Root").one().id
    register(client, "mallory")
    client.post("/auth/logout")
    login(client, "mallory")

    response = client.get(f"/family-trees/{tree_id}/tree-preview?root_member_id={root_id}")

    assert response.status_code == 403


def test_collaborator_can_view_tree_preview(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Root")
    register(client, "bob")
    with app.app_context():
        root_id = Member.query.filter_by(name="Root").one().id
        bob = User.query.filter_by(username="bob").one()
        db.session.add(FamilyTreeCollaborator(family_tree_id=tree_id, user_id=bob.id))
        db.session.commit()
    client.post("/auth/logout")
    login(client, "bob")

    response = client.get(f"/family-trees/{tree_id}/tree-preview?root_member_id={root_id}")

    assert response.status_code == 200
    assert b"Root" in response.data


def test_tree_preview_marks_cycle_without_infinite_recursion(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "A")
    create_member(client, tree_id, "B")
    with app.app_context():
        member_a = Member.query.filter_by(name="A").one()
        member_b = Member.query.filter_by(name="B").one()
        db.session.add(
            ParentChildRelationship(
                family_tree_id=tree_id,
                parent_id=member_a.id,
                child_id=member_b.id,
                relationship_type="father",
            )
        )
        db.session.add(
            ParentChildRelationship(
                family_tree_id=tree_id,
                parent_id=member_b.id,
                child_id=member_a.id,
                relationship_type="mother",
            )
        )
        db.session.commit()
        root_id = member_a.id

    response = client.get(f"/family-trees/{tree_id}/tree-preview?root_member_id={root_id}")

    assert response.status_code == 200
    assert b"cycle detected" in response.data
