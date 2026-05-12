import pytest

from app import create_app
from app.extensions import db
from app.models import FamilyTree, FamilyTreeCollaborator, Member, User


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
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )


def create_family_tree(client, name="Chen Genealogy", surname="Chen"):
    return client.post(
        "/family-trees/new",
        data={"name": name, "surname": surname, "revision_time": ""},
    )


def create_member(
    client,
    tree_id,
    name="Chen Ming",
    gender="male",
    birth_year="1970",
    death_year="",
    generation="12",
    biography="A short biography.",
):
    return client.post(
        f"/family-trees/{tree_id}/members/new",
        data={
            "name": name,
            "gender": gender,
            "birth_year": birth_year,
            "death_year": death_year,
            "generation": generation,
            "biography": biography,
        },
    )


def setup_tree(app, client, username="alice"):
    register(client, username)
    login(client, username)
    create_family_tree(client)
    with app.app_context():
        return FamilyTree.query.filter_by(name="Chen Genealogy").one().id


def test_login_required_for_member_pages(client):
    response = client.get("/family-trees/1/members")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_accessible_user_can_create_member(app, client):
    tree_id = setup_tree(app, client)

    response = create_member(client, tree_id)

    assert response.status_code == 302
    with app.app_context():
        member = Member.query.filter_by(name="Chen Ming").one()
        assert member.family_tree_id == tree_id
        assert member.gender == "male"
        assert member.birth_year == 1970
        assert member.generation == 12


def test_member_list_and_detail_show_member(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, name="Chen Li")

    response = client.get(f"/family-trees/{tree_id}/members")
    assert response.status_code == 200
    assert b"Chen Li" in response.data

    with app.app_context():
        member = Member.query.filter_by(name="Chen Li").one()

    response = client.get(f"/family-trees/{tree_id}/members/{member.id}")
    assert response.status_code == 200
    assert b"Chen Li" in response.data


def test_member_can_be_edited(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, name="Chen Old")

    with app.app_context():
        member = Member.query.filter_by(name="Chen Old").one()

    response = client.post(
        f"/family-trees/{tree_id}/members/{member.id}/edit",
        data={
            "name": "Chen New",
            "gender": "female",
            "birth_year": "1980",
            "death_year": "",
            "generation": "13",
            "biography": "Updated.",
        },
    )

    assert response.status_code == 302
    with app.app_context():
        updated = db.session.get(Member, member.id)
        assert updated.name == "Chen New"
        assert updated.gender == "female"
        assert updated.biography == "Updated."


def test_member_can_be_deleted(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id)

    with app.app_context():
        member = Member.query.filter_by(name="Chen Ming").one()

    response = client.post(f"/family-trees/{tree_id}/members/{member.id}/delete")

    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Member, member.id) is None


def test_member_search_is_fuzzy_and_scoped_to_tree(app, client):
    tree_id = setup_tree(app, client)
    create_member(client, tree_id, name="Chen Ming")
    create_member(client, tree_id, name="Li Hua")

    with app.app_context():
        other_user = User(username="bob", display_name="Bob", password_hash="hash")
        db.session.add(other_user)
        db.session.flush()
        other_tree = FamilyTree(
            name="Other Tree",
            surname="Wang",
            created_by_user_id=other_user.id,
        )
        db.session.add(other_tree)
        db.session.flush()
        db.session.add(Member(family_tree_id=other_tree.id, name="Chen Hidden"))
        db.session.commit()

    response = client.get(f"/family-trees/{tree_id}/members?q=Chen")

    assert response.status_code == 200
    assert b"Chen Ming" in response.data
    assert b"Li Hua" not in response.data
    assert b"Chen Hidden" not in response.data


def test_collaborator_can_manage_members(app, client):
    tree_id = setup_tree(app, client, username="alice")
    register(client, "bob")

    with app.app_context():
        bob = User.query.filter_by(username="bob").one()
        db.session.add(FamilyTreeCollaborator(family_tree_id=tree_id, user_id=bob.id))
        db.session.commit()

    client.post("/auth/logout")
    login(client, "bob")

    response = create_member(client, tree_id, name="Collaborator Member")

    assert response.status_code == 302
    with app.app_context():
        assert Member.query.filter_by(name="Collaborator Member").one()


def test_uninvited_user_cannot_manage_members(app, client):
    tree_id = setup_tree(app, client, username="alice")
    register(client, "mallory")
    client.post("/auth/logout")
    login(client, "mallory")

    response = client.get(f"/family-trees/{tree_id}/members")

    assert response.status_code == 403


def test_member_from_other_tree_returns_404(app, client):
    tree_id = setup_tree(app, client, username="alice")

    with app.app_context():
        other_tree = FamilyTree(name="Other Tree", surname="Li", created_by_user_id=1)
        db.session.add(other_tree)
        db.session.flush()
        other_member = Member(family_tree_id=other_tree.id, name="Other Member")
        db.session.add(other_member)
        db.session.commit()
        other_member_id = other_member.id

    response = client.get(f"/family-trees/{tree_id}/members/{other_member_id}")

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("data_override", "message"),
    (
        ({"name": ""}, b"Name is required"),
        ({"gender": "invalid"}, b"Gender is invalid"),
        ({"birth_year": "abc"}, b"Birth year must be an integer"),
        ({"death_year": "abc"}, b"Death year must be an integer"),
        ({"generation": "0"}, b"Generation must be greater than 0"),
        (
            {"birth_year": "2000", "death_year": "1999"},
            b"Death year must be greater than or equal to birth year",
        ),
    ),
)
def test_member_form_validation(app, client, data_override, message):
    tree_id = setup_tree(app, client)
    data = {
        "name": "Chen Ming",
        "gender": "male",
        "birth_year": "1970",
        "death_year": "",
        "generation": "12",
        "biography": "",
    }
    data.update(data_override)

    response = client.post(f"/family-trees/{tree_id}/members/new", data=data)

    assert response.status_code == 400
    assert message in response.data
