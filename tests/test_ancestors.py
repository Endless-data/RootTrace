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


def add_parent_child(tree_id, parent_id, child_id, relationship_type="father"):
    db.session.add(
        ParentChildRelationship(
            family_tree_id=tree_id,
            parent_id=parent_id,
            child_id=child_id,
            relationship_type=relationship_type,
        )
    )


def test_login_required_for_ancestor_query(client):
    response = client.get("/family-trees/1/ancestors")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_ancestor_query_shows_empty_state(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Root")
    with app.app_context():
        member_id = Member.query.filter_by(name="Root").one().id

    response = client.get(f"/family-trees/{tree_id}/ancestors?member_id={member_id}")

    assert response.status_code == 200
    assert b"No known ancestors" in response.data
    assert b"Root" in response.data


def test_ancestor_query_shows_multiple_generations(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Grandparent", generation="1")
    create_member(client, tree_id, "Parent", generation="2")
    create_member(client, tree_id, "Child", generation="3")
    with app.app_context():
        grandparent = Member.query.filter_by(name="Grandparent").one()
        parent = Member.query.filter_by(name="Parent").one()
        child = Member.query.filter_by(name="Child").one()
        add_parent_child(tree_id, grandparent.id, parent.id, "father")
        add_parent_child(tree_id, parent.id, child.id, "father")
        db.session.commit()
        child_id = child.id
        parent_id = parent.id
        grandparent_id = grandparent.id

    response = client.get(f"/family-trees/{tree_id}/ancestors?member_id={child_id}")

    assert response.status_code == 200
    assert b"Ancestors of Child" in response.data
    assert f"#{child_id}".encode() in response.data
    assert f"#{parent_id}".encode() in response.data
    assert f"#{grandparent_id}".encode() in response.data


def test_ancestor_query_shows_both_parent_branches(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Father")
    create_member(client, tree_id, "Mother")
    create_member(client, tree_id, "Child")
    with app.app_context():
        father = Member.query.filter_by(name="Father").one()
        mother = Member.query.filter_by(name="Mother").one()
        child = Member.query.filter_by(name="Child").one()
        add_parent_child(tree_id, father.id, child.id, "father")
        add_parent_child(tree_id, mother.id, child.id, "mother")
        db.session.commit()
        child_id = child.id

    response = client.get(f"/family-trees/{tree_id}/ancestors?member_id={child_id}")

    assert response.status_code == 200
    assert b"Father" in response.data
    assert b"Mother" in response.data


def test_ancestor_query_disambiguates_duplicate_names_by_id(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Chen Ming", generation="1")
    create_member(client, tree_id, "Chen Ming", generation="2")
    with app.app_context():
        older = Member.query.filter_by(generation=1).one()
        younger = Member.query.filter_by(generation=2).one()
        add_parent_child(tree_id, older.id, younger.id, "father")
        db.session.commit()
        older_id = older.id
        younger_id = younger.id

    response = client.get(f"/family-trees/{tree_id}/ancestors?member_id={younger_id}")

    assert response.status_code == 200
    assert b"Chen Ming" in response.data
    assert f"#{older_id}".encode() in response.data
    assert f"#{younger_id}".encode() in response.data


def test_ancestor_query_rejects_member_from_other_tree(app, client):
    tree_id = setup_tree(app, client)
    with app.app_context():
        alice = User.query.filter_by(username="alice").one()
        other_tree = FamilyTree(name="Other", surname="Li", created_by_user_id=alice.id)
        db.session.add(other_tree)
        db.session.flush()
        other_member = Member(family_tree_id=other_tree.id, name="Other")
        db.session.add(other_member)
        db.session.commit()
        other_member_id = other_member.id

    response = client.get(f"/family-trees/{tree_id}/ancestors?member_id={other_member_id}")

    assert response.status_code == 404


def test_uninvited_user_cannot_query_ancestors(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Root")
    with app.app_context():
        member_id = Member.query.filter_by(name="Root").one().id
    register(client, "mallory")
    client.post("/auth/logout")
    login(client, "mallory")

    response = client.get(f"/family-trees/{tree_id}/ancestors?member_id={member_id}")

    assert response.status_code == 403


def test_collaborator_can_query_ancestors(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Root")
    register(client, "bob")
    with app.app_context():
        member_id = Member.query.filter_by(name="Root").one().id
        bob = User.query.filter_by(username="bob").one()
        db.session.add(FamilyTreeCollaborator(family_tree_id=tree_id, user_id=bob.id))
        db.session.commit()
    client.post("/auth/logout")
    login(client, "bob")

    response = client.get(f"/family-trees/{tree_id}/ancestors?member_id={member_id}")

    assert response.status_code == 200
    assert b"Root" in response.data


def test_ancestor_query_marks_cycle_without_infinite_recursion(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "A")
    create_member(client, tree_id, "B")
    with app.app_context():
        member_a = Member.query.filter_by(name="A").one()
        member_b = Member.query.filter_by(name="B").one()
        add_parent_child(tree_id, member_a.id, member_b.id, "father")
        add_parent_child(tree_id, member_b.id, member_a.id, "mother")
        db.session.commit()
        member_a_id = member_a.id

    response = client.get(f"/family-trees/{tree_id}/ancestors?member_id={member_a_id}")

    assert response.status_code == 200
    assert b"cycle detected" in response.data
