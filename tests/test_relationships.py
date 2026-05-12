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


def create_member(client, tree_id, name, gender="unknown", birth_year="", generation=""):
    return client.post(
        f"/family-trees/{tree_id}/members/new",
        data={
            "name": name,
            "gender": gender,
            "birth_year": birth_year,
            "death_year": "",
            "generation": generation,
            "biography": "",
        },
    )


def setup_tree_with_members(app, client):
    register(client, "alice")
    login(client, "alice")
    create_family_tree(client)
    with app.app_context():
        tree_id = FamilyTree.query.filter_by(name="Chen Genealogy").one().id
    create_member(client, tree_id, "Parent", birth_year="1940")
    create_member(client, tree_id, "Child", birth_year="1970")
    create_member(client, tree_id, "Spouse", birth_year="1972")
    with app.app_context():
        parent = Member.query.filter_by(name="Parent").one()
        child = Member.query.filter_by(name="Child").one()
        spouse = Member.query.filter_by(name="Spouse").one()
        return tree_id, parent.id, child.id, spouse.id


def test_login_required_for_relationship_page(client):
    response = client.get("/family-trees/1/members/1/relationships")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_can_add_parent_relationship(app, client):
    tree_id, parent_id, child_id, _ = setup_tree_with_members(app, client)

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data={"parent_id": str(parent_id), "relationship_type": "father"},
    )

    assert response.status_code == 302
    with app.app_context():
        relationship = ParentChildRelationship.query.one()
        assert relationship.parent_id == parent_id
        assert relationship.child_id == child_id
        assert relationship.relationship_type == "father"


def test_can_add_child_relationship(app, client):
    tree_id, parent_id, child_id, _ = setup_tree_with_members(app, client)

    response = client.post(
        f"/family-trees/{tree_id}/members/{parent_id}/relationships/children",
        data={"child_id": str(child_id), "relationship_type": "mother"},
    )

    assert response.status_code == 302
    with app.app_context():
        relationship = ParentChildRelationship.query.one()
        assert relationship.parent_id == parent_id
        assert relationship.child_id == child_id
        assert relationship.relationship_type == "mother"


def test_relationship_page_lists_parent_child_and_spouse(app, client):
    tree_id, parent_id, child_id, spouse_id = setup_tree_with_members(app, client)
    client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data={"parent_id": str(parent_id), "relationship_type": "father"},
    )
    client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/marriages",
        data={"spouse_id": str(spouse_id), "start_year": "1990", "end_year": ""},
    )

    response = client.get(f"/family-trees/{tree_id}/members/{child_id}/relationships")

    assert response.status_code == 200
    assert b"Parent" in response.data
    assert b"Spouse" in response.data


def test_can_delete_parent_child_relationship(app, client):
    tree_id, parent_id, child_id, _ = setup_tree_with_members(app, client)
    client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data={"parent_id": str(parent_id), "relationship_type": "father"},
    )
    with app.app_context():
        relationship_id = ParentChildRelationship.query.one().id

    response = client.post(
        f"/family-trees/{tree_id}/relationships/parent-child/{relationship_id}/delete"
    )

    assert response.status_code == 302
    with app.app_context():
        assert ParentChildRelationship.query.count() == 0


def test_can_add_and_delete_marriage(app, client):
    tree_id, _, child_id, spouse_id = setup_tree_with_members(app, client)

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/marriages",
        data={"spouse_id": str(spouse_id), "start_year": "1990", "end_year": "2020"},
    )

    assert response.status_code == 302
    with app.app_context():
        marriage = Marriage.query.one()
        assert {marriage.person_a_id, marriage.person_b_id} == {child_id, spouse_id}
        marriage_id = marriage.id

    response = client.post(
        f"/family-trees/{tree_id}/relationships/marriages/{marriage_id}/delete"
    )

    assert response.status_code == 302
    with app.app_context():
        assert Marriage.query.count() == 0


def test_collaborator_can_manage_relationships(app, client):
    tree_id, parent_id, child_id, _ = setup_tree_with_members(app, client)
    register(client, "bob")
    with app.app_context():
        bob = User.query.filter_by(username="bob").one()
        db.session.add(FamilyTreeCollaborator(family_tree_id=tree_id, user_id=bob.id))
        db.session.commit()
    client.post("/auth/logout")
    login(client, "bob")

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data={"parent_id": str(parent_id), "relationship_type": "father"},
    )

    assert response.status_code == 302
    with app.app_context():
        assert ParentChildRelationship.query.count() == 1


def test_uninvited_user_cannot_manage_relationships(app, client):
    tree_id, parent_id, child_id, _ = setup_tree_with_members(app, client)
    register(client, "mallory")
    client.post("/auth/logout")
    login(client, "mallory")

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data={"parent_id": str(parent_id), "relationship_type": "father"},
    )

    assert response.status_code == 403


def test_rejects_member_from_other_tree(app, client):
    tree_id, _, child_id, _ = setup_tree_with_members(app, client)
    with app.app_context():
        alice = User.query.filter_by(username="alice").one()
        other_tree = FamilyTree(name="Other", surname="Li", created_by_user_id=alice.id)
        db.session.add(other_tree)
        db.session.flush()
        other_member = Member(family_tree_id=other_tree.id, name="Other")
        db.session.add(other_member)
        db.session.commit()
        other_member_id = other_member.id

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data={"parent_id": str(other_member_id), "relationship_type": "father"},
    )

    assert response.status_code == 400
    assert b"Member must belong to this family tree" in response.data


@pytest.mark.parametrize(
    ("relationship_type", "message"),
    (
        ("invalid", b"Relationship type is invalid"),
        ("father", b"A member cannot be their own parent"),
    ),
)
def test_rejects_invalid_parent_child_relationship(app, client, relationship_type, message):
    tree_id, _, child_id, _ = setup_tree_with_members(app, client)
    parent_id = child_id if relationship_type == "father" else child_id - 1

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data={"parent_id": str(parent_id), "relationship_type": relationship_type},
    )

    assert response.status_code == 400
    assert message in response.data


def test_rejects_duplicate_parent_child_relationship(app, client):
    tree_id, parent_id, child_id, _ = setup_tree_with_members(app, client)
    payload = {"parent_id": str(parent_id), "relationship_type": "father"}
    client.post(f"/family-trees/{tree_id}/members/{child_id}/relationships/parents", data=payload)

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data=payload,
    )

    assert response.status_code == 400
    assert b"already exists" in response.data


def test_rejects_second_father(app, client):
    tree_id, parent_id, child_id, _ = setup_tree_with_members(app, client)
    create_member(client, tree_id, "Second Father", birth_year="1945")
    with app.app_context():
        second_father_id = Member.query.filter_by(name="Second Father").one().id
    client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data={"parent_id": str(parent_id), "relationship_type": "father"},
    )

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data={"parent_id": str(second_father_id), "relationship_type": "father"},
    )

    assert response.status_code == 400
    assert b"already has a father" in response.data


def test_rejects_parent_birth_year_not_earlier(app, client):
    tree_id = setup_tree_with_members(app, client)[0]
    create_member(client, tree_id, "Young Parent", birth_year="2000")
    create_member(client, tree_id, "Old Child", birth_year="1980")
    with app.app_context():
        parent_id = Member.query.filter_by(name="Young Parent").one().id
        child_id = Member.query.filter_by(name="Old Child").one().id

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/parents",
        data={"parent_id": str(parent_id), "relationship_type": "father"},
    )

    assert response.status_code == 400
    assert b"Parent birth year must be earlier" in response.data


def test_rejects_self_marriage_and_duplicate_marriage(app, client):
    tree_id, _, child_id, spouse_id = setup_tree_with_members(app, client)

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/marriages",
        data={"spouse_id": str(child_id), "start_year": "", "end_year": ""},
    )

    assert response.status_code == 400
    assert b"cannot marry themselves" in response.data

    payload = {"spouse_id": str(spouse_id), "start_year": "", "end_year": ""}
    client.post(f"/family-trees/{tree_id}/members/{child_id}/relationships/marriages", data=payload)
    response = client.post(
        f"/family-trees/{tree_id}/members/{spouse_id}/relationships/marriages",
        data={"spouse_id": str(child_id), "start_year": "", "end_year": ""},
    )

    assert response.status_code == 400
    assert b"Marriage relationship already exists" in response.data


def test_rejects_invalid_marriage_years(app, client):
    tree_id, _, child_id, spouse_id = setup_tree_with_members(app, client)

    response = client.post(
        f"/family-trees/{tree_id}/members/{child_id}/relationships/marriages",
        data={"spouse_id": str(spouse_id), "start_year": "2020", "end_year": "1990"},
    )

    assert response.status_code == 400
    assert b"Marriage end year must be greater than or equal to start year" in response.data
