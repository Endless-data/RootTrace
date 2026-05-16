import pytest

from app import create_app
from app.extensions import db
from app.models import FamilyTree, FamilyTreeCollaborator, User


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


def create_family_tree(client, name="Chen Genealogy", surname="Chen", revision_time=""):
    return client.post(
        "/family-trees/new",
        data={"name": name, "surname": surname, "revision_time": revision_time},
    )


def test_login_required_for_family_tree_pages(client):
    response = client.get("/family-trees")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_user_can_create_family_tree(app, client):
    register(client, "alice", "Alice")
    login(client, "alice")

    response = create_family_tree(client, revision_time="2026-05-09")

    assert response.status_code == 302
    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()
        creator = User.query.filter_by(username="alice").one()
        assert family_tree.surname == "Chen"
        assert family_tree.created_by_user_id == creator.id
        assert family_tree.revision_time.isoformat() == "2026-05-09"


def test_family_tree_list_shows_created_and_collaborated_trees(app, client):
    register(client, "alice", "Alice")
    register(client, "bob", "Bob")
    login(client, "alice")
    create_family_tree(client, name="Alice Tree", surname="Li")

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Alice Tree").one()
        bob = User.query.filter_by(username="bob").one()
        db.session.add(FamilyTreeCollaborator(family_tree_id=family_tree.id, user_id=bob.id))
        db.session.commit()

    client.post("/auth/logout")
    login(client, "bob")
    response = client.get("/family-trees")

    assert response.status_code == 200
    assert b"Alice Tree" in response.data


def test_creator_can_invite_existing_user(app, client):
    register(client, "alice", "Alice")
    register(client, "bob", "Bob")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    response = client.post(
        f"/family-trees/{family_tree.id}/collaborators",
        data={"username": "bob"},
    )

    assert response.status_code == 302
    with app.app_context():
        bob = User.query.filter_by(username="bob").one()
        collaboration = FamilyTreeCollaborator.query.filter_by(
            family_tree_id=family_tree.id,
            user_id=bob.id,
        ).one()
        assert collaboration.role == "editor"


def test_invited_user_can_access_family_tree(app, client):
    register(client, "alice", "Alice")
    register(client, "bob", "Bob")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    client.post(
        f"/family-trees/{family_tree.id}/collaborators",
        data={"username": "bob"},
    )
    client.post("/auth/logout")
    login(client, "bob")

    response = client.get(f"/family-trees/{family_tree.id}")

    assert response.status_code == 200
    assert b"Chen Genealogy" in response.data


def test_family_tree_detail_links_to_import_export(app, client):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    response = client.get(f"/family-trees/{family_tree.id}")

    assert response.status_code == 200
    assert "导入导出".encode() in response.data
    assert f"/family-trees/{family_tree.id}/import-export".encode() in response.data


def test_creator_can_view_import_export_page(app, client):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    response = client.get(f"/family-trees/{family_tree.id}/import-export")

    assert response.status_code == 200
    assert "批量导入".encode() in response.data
    assert b"sql/import_simulated_data.sql" in response.data
    assert b"sql/export_branch.sql" in response.data


def test_collaborator_can_view_import_export_page(app, client):
    register(client, "alice", "Alice")
    register(client, "bob", "Bob")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    client.post(
        f"/family-trees/{family_tree.id}/collaborators",
        data={"username": "bob"},
    )
    client.post("/auth/logout")
    login(client, "bob")

    response = client.get(f"/family-trees/{family_tree.id}/import-export")

    assert response.status_code == 200
    assert "分支导出".encode() in response.data


def test_uninvited_user_cannot_access_family_tree(app, client):
    register(client, "alice", "Alice")
    register(client, "mallory", "Mallory")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    client.post("/auth/logout")
    login(client, "mallory")

    response = client.get(f"/family-trees/{family_tree.id}")

    assert response.status_code == 403


def test_uninvited_user_cannot_view_import_export_page(app, client):
    register(client, "alice", "Alice")
    register(client, "mallory", "Mallory")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    client.post("/auth/logout")
    login(client, "mallory")

    response = client.get(f"/family-trees/{family_tree.id}/import-export")

    assert response.status_code == 403


def test_non_creator_cannot_invite_collaborator(app, client):
    register(client, "alice", "Alice")
    register(client, "bob", "Bob")
    register(client, "carol", "Carol")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    client.post(
        f"/family-trees/{family_tree.id}/collaborators",
        data={"username": "bob"},
    )
    client.post("/auth/logout")
    login(client, "bob")

    response = client.post(
        f"/family-trees/{family_tree.id}/collaborators",
        data={"username": "carol"},
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("username", "message"),
    (
        ("unknown", b"User does not exist"),
        ("alice", b"Creator cannot be invited"),
    ),
)
def test_invitation_rejects_invalid_user(app, client, username, message):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    response = client.post(
        f"/family-trees/{family_tree.id}/collaborators",
        data={"username": username},
    )

    assert response.status_code == 400
    assert message in response.data


def test_invitation_rejects_duplicate_collaborator(app, client):
    register(client, "alice", "Alice")
    register(client, "bob", "Bob")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    client.post(
        f"/family-trees/{family_tree.id}/collaborators",
        data={"username": "bob"},
    )
    response = client.post(
        f"/family-trees/{family_tree.id}/collaborators",
        data={"username": "bob"},
    )

    assert response.status_code == 400
    assert b"already a collaborator" in response.data
