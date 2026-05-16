import pytest

from app import create_app
from app.extensions import db
from app.models import FamilyTree, FamilyTreeCollaborator, Marriage, Member, ParentChildRelationship, User


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


def member_id_by_name(name):
    return Member.query.filter_by(name=name).one().id


def add_parent_child(tree_id, parent_id, child_id, relationship_type="father"):
    db.session.add(
        ParentChildRelationship(
            family_tree_id=tree_id,
            parent_id=parent_id,
            child_id=child_id,
            relationship_type=relationship_type,
        )
    )


def add_marriage(tree_id, person_a_id, person_b_id):
    db.session.add(
        Marriage(
            family_tree_id=tree_id,
            person_a_id=person_a_id,
            person_b_id=person_b_id,
        )
    )


def test_login_required_for_relationship_path_query(client):
    response = client.get("/family-trees/1/relationship-path")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_relationship_path_shows_direct_parent_child_edge(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Parent")
    create_member(client, tree_id, "Child")
    with app.app_context():
        parent_id = member_id_by_name("Parent")
        child_id = member_id_by_name("Child")
        add_parent_child(tree_id, parent_id, child_id, "father")
        db.session.commit()

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={parent_id}&target_member_id={child_id}"
    )

    assert response.status_code == 200
    assert "已找到路径".encode() in response.data
    assert b"Parent" in response.data
    assert b"Child" in response.data
    assert b"father-child" in response.data


def test_relationship_path_shows_multi_generation_path(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Grandparent")
    create_member(client, tree_id, "Parent")
    create_member(client, tree_id, "Child")
    with app.app_context():
        grandparent_id = member_id_by_name("Grandparent")
        parent_id = member_id_by_name("Parent")
        child_id = member_id_by_name("Child")
        add_parent_child(tree_id, grandparent_id, parent_id, "father")
        add_parent_child(tree_id, parent_id, child_id, "mother")
        db.session.commit()

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={grandparent_id}&target_member_id={child_id}"
    )

    assert response.status_code == 200
    assert b"Grandparent" in response.data
    assert b"Parent" in response.data
    assert b"Child" in response.data
    assert b"father-child" in response.data
    assert b"mother-child" in response.data


def test_relationship_path_includes_marriage_edges(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Person A")
    create_member(client, tree_id, "Person B")
    with app.app_context():
        person_a_id = member_id_by_name("Person A")
        person_b_id = member_id_by_name("Person B")
        add_marriage(tree_id, person_a_id, person_b_id)
        db.session.commit()

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={person_b_id}&target_member_id={person_a_id}"
    )

    assert response.status_code == 200
    assert b"Person A" in response.data
    assert b"Person B" in response.data
    assert b"spouse" in response.data


def test_relationship_path_combines_marriage_and_blood_edges(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Father")
    create_member(client, tree_id, "Mother")
    create_member(client, tree_id, "Child")
    with app.app_context():
        father_id = member_id_by_name("Father")
        mother_id = member_id_by_name("Mother")
        child_id = member_id_by_name("Child")
        add_marriage(tree_id, father_id, mother_id)
        add_parent_child(tree_id, mother_id, child_id, "mother")
        db.session.commit()

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={father_id}&target_member_id={child_id}"
    )

    assert response.status_code == 200
    assert b"spouse" in response.data
    assert b"mother-child" in response.data


def test_relationship_path_shows_no_path_state(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "A")
    create_member(client, tree_id, "B")
    with app.app_context():
        member_a_id = member_id_by_name("A")
        member_b_id = member_id_by_name("B")

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={member_a_id}&target_member_id={member_b_id}"
    )

    assert response.status_code == 200
    assert "未找到亲缘路径。".encode() in response.data


def test_relationship_path_handles_same_member(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Same")
    with app.app_context():
        member_id = member_id_by_name("Same")

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={member_id}&target_member_id={member_id}"
    )

    assert response.status_code == 200
    assert "同一成员".encode() in response.data
    assert f"#{member_id}".encode() in response.data


def test_relationship_path_rejects_member_from_other_tree(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Local")
    with app.app_context():
        alice = User.query.filter_by(username="alice").one()
        other_tree = FamilyTree(name="Other", surname="Li", created_by_user_id=alice.id)
        db.session.add(other_tree)
        db.session.flush()
        other_member = Member(family_tree_id=other_tree.id, name="Other")
        db.session.add(other_member)
        db.session.commit()
        local_id = member_id_by_name("Local")
        other_member_id = other_member.id

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={local_id}&target_member_id={other_member_id}"
    )

    assert response.status_code == 404


def test_uninvited_user_cannot_query_relationship_path(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "A")
    create_member(client, tree_id, "B")
    with app.app_context():
        member_a_id = member_id_by_name("A")
        member_b_id = member_id_by_name("B")
    register(client, "mallory")
    client.post("/auth/logout")
    login(client, "mallory")

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={member_a_id}&target_member_id={member_b_id}"
    )

    assert response.status_code == 403


def test_collaborator_can_query_relationship_path(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "A")
    create_member(client, tree_id, "B")
    register(client, "bob")
    with app.app_context():
        member_a_id = member_id_by_name("A")
        member_b_id = member_id_by_name("B")
        add_parent_child(tree_id, member_a_id, member_b_id)
        bob = User.query.filter_by(username="bob").one()
        db.session.add(FamilyTreeCollaborator(family_tree_id=tree_id, user_id=bob.id))
        db.session.commit()
    client.post("/auth/logout")
    login(client, "bob")

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={member_a_id}&target_member_id={member_b_id}"
    )

    assert response.status_code == 200
    assert "已找到路径".encode() in response.data


def test_relationship_path_disambiguates_duplicate_names_by_id(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "Chen Ming", generation="1")
    create_member(client, tree_id, "Chen Ming", generation="2")
    with app.app_context():
        older = Member.query.filter_by(generation=1).one()
        younger = Member.query.filter_by(generation=2).one()
        add_parent_child(tree_id, older.id, younger.id)
        db.session.commit()
        older_id = older.id
        younger_id = younger.id

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={older_id}&target_member_id={younger_id}"
    )

    assert response.status_code == 200
    assert b"Chen Ming" in response.data
    assert f"#{older_id}".encode() in response.data
    assert f"#{younger_id}".encode() in response.data


def test_relationship_path_handles_cycles(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, "A")
    create_member(client, tree_id, "B")
    create_member(client, tree_id, "C")
    with app.app_context():
        member_a_id = member_id_by_name("A")
        member_b_id = member_id_by_name("B")
        member_c_id = member_id_by_name("C")
        add_parent_child(tree_id, member_a_id, member_b_id)
        add_parent_child(tree_id, member_b_id, member_a_id)
        add_parent_child(tree_id, member_b_id, member_c_id)
        db.session.commit()

    response = client.get(
        f"/family-trees/{tree_id}/relationship-path"
        f"?source_member_id={member_a_id}&target_member_id={member_c_id}"
    )

    assert response.status_code == 200
    assert "已找到路径".encode() in response.data
    assert b"C" in response.data
