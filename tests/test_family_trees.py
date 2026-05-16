import io
import zipfile

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
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )


def create_family_tree(client, name="Chen Genealogy", surname="Chen", revision_time=""):
    return client.post(
        "/family-trees/new",
        data={"name": name, "surname": surname, "revision_time": revision_time},
    )


def csv_upload(content, filename):
    return io.BytesIO(content.encode("utf-8")), filename


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


def test_family_tree_detail_shows_owner_edit_and_delete_actions(app, client):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    response = client.get(f"/family-trees/{family_tree.id}")

    assert response.status_code == 200
    assert "编辑族谱".encode() in response.data
    assert f"/family-trees/{family_tree.id}/edit".encode() in response.data
    assert "删除族谱".encode() in response.data
    assert f"/family-trees/{family_tree.id}/delete".encode() in response.data


def test_creator_can_edit_family_tree(app, client):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()
        tree_id = family_tree.id

    response = client.post(
        f"/family-trees/{tree_id}/edit",
        data={"name": "Updated Genealogy", "surname": "Li", "revision_time": "2026-05-16"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/family-trees/{tree_id}")
    with app.app_context():
        updated = db.session.get(FamilyTree, tree_id)
        assert updated.name == "Updated Genealogy"
        assert updated.surname == "Li"
        assert updated.revision_time.isoformat() == "2026-05-16"


@pytest.mark.parametrize(
    ("data", "message"),
    (
        ({"name": "", "surname": "Chen", "revision_time": ""}, b"Family tree name is required"),
        ({"name": "Chen Genealogy", "surname": "", "revision_time": ""}, b"Surname is required"),
        ({"name": "Chen Genealogy", "surname": "Chen", "revision_time": "invalid"}, b"Invalid revision date"),
    ),
)
def test_family_tree_edit_validates_input(app, client, data, message):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    response = client.post(f"/family-trees/{family_tree.id}/edit", data=data)

    assert response.status_code == 400
    assert message in response.data


def test_collaborator_cannot_edit_family_tree(app, client):
    register(client, "alice", "Alice")
    register(client, "bob", "Bob")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()
        tree_id = family_tree.id

    client.post(
        f"/family-trees/{tree_id}/collaborators",
        data={"username": "bob"},
    )
    client.post("/auth/logout")
    login(client, "bob")

    response = client.post(
        f"/family-trees/{tree_id}/edit",
        data={"name": "Bob Update", "surname": "Bob", "revision_time": ""},
    )

    assert response.status_code == 403
    with app.app_context():
        family_tree = db.session.get(FamilyTree, tree_id)
        assert family_tree.name == "Chen Genealogy"


def test_creator_can_view_import_export_page(app, client):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()

    response = client.get(f"/family-trees/{family_tree.id}/import-export")

    assert response.status_code == 200
    assert "CSV 导入".encode() in response.data
    assert b'name="members_csv"' in response.data
    assert f"/family-trees/{family_tree.id}/export.zip".encode() in response.data


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
    assert "CSV 导出".encode() in response.data


def test_creator_can_export_family_tree_zip(app, client):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()
        parent = Member(family_tree_id=family_tree.id, name="Parent", gender="male", generation=1)
        child = Member(family_tree_id=family_tree.id, name="Child", gender="female", generation=2)
        db.session.add_all([parent, child])
        db.session.flush()
        db.session.add(
            ParentChildRelationship(
                family_tree_id=family_tree.id,
                parent_id=parent.id,
                child_id=child.id,
                relationship_type="father",
            )
        )
        db.session.add(
            Marriage(
                family_tree_id=family_tree.id,
                person_a_id=parent.id,
                person_b_id=child.id,
                start_year=1990,
            )
        )
        db.session.commit()
        tree_id = family_tree.id

    response = client.get(f"/family-trees/{tree_id}/export.zip")

    assert response.status_code == 200
    assert response.mimetype == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        assert sorted(archive.namelist()) == [
            "marriages.csv",
            "members.csv",
            "parent_child_relationships.csv",
        ]
        members_csv = archive.read("members.csv").decode("utf-8")
        relationships_csv = archive.read("parent_child_relationships.csv").decode("utf-8")
        marriages_csv = archive.read("marriages.csv").decode("utf-8")

    assert "id,family_tree_id,name,gender,birth_year,death_year,generation,biography,created_at" in members_csv
    assert "Parent" in members_csv
    assert "parent_id,child_id,relationship_type" in relationships_csv
    assert "person_a_id,person_b_id,start_year,end_year" in marriages_csv


def test_creator_can_import_members_csv(app, client):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()
        tree_id = family_tree.id

    members_csv = "\n".join(
        [
            "id,family_tree_id,name,gender,birth_year,death_year,generation,biography,created_at",
            "10,999,Imported Parent,male,1940,,1,Imported biography,",
        ]
    )
    response = client.post(
        f"/family-trees/{tree_id}/import",
        data={"members_csv": csv_upload(members_csv, "members.csv")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert "导入完成".encode() in response.data
    with app.app_context():
        member = Member.query.filter_by(name="Imported Parent").one()
        assert member.family_tree_id == tree_id
        assert member.biography == "Imported biography"


def test_creator_can_import_relationship_csvs(app, client):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()
        tree_id = family_tree.id

    members_csv = "\n".join(
        [
            "id,family_tree_id,name,gender,birth_year,death_year,generation,biography,created_at",
            "1,999,Imported Parent,male,1940,,1,,",
            "2,999,Imported Child,female,1970,,2,,",
        ]
    )
    parent_child_csv = "\n".join(
        [
            "id,family_tree_id,parent_id,child_id,relationship_type",
            "1,999,1,2,father",
        ]
    )
    marriages_csv = "\n".join(
        [
            "id,family_tree_id,person_a_id,person_b_id,start_year,end_year",
            "1,999,1,2,1990,",
        ]
    )

    response = client.post(
        f"/family-trees/{tree_id}/import",
        data={
            "members_csv": csv_upload(members_csv, "members.csv"),
            "parent_child_relationships_csv": csv_upload(parent_child_csv, "parent_child_relationships.csv"),
            "marriages_csv": csv_upload(marriages_csv, "marriages.csv"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    with app.app_context():
        parent = Member.query.filter_by(name="Imported Parent").one()
        child = Member.query.filter_by(name="Imported Child").one()
        relationship = ParentChildRelationship.query.one()
        marriage = Marriage.query.one()
        assert relationship.family_tree_id == tree_id
        assert relationship.parent_id == parent.id
        assert relationship.child_id == child.id
        assert marriage.family_tree_id == tree_id
        assert {marriage.person_a_id, marriage.person_b_id} == {parent.id, child.id}


def test_import_rolls_back_when_relationship_references_unknown_member(app, client):
    register(client, "alice", "Alice")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()
        tree_id = family_tree.id

    members_csv = "\n".join(
        [
            "id,family_tree_id,name,gender,birth_year,death_year,generation,biography,created_at",
            "1,999,Imported Parent,male,1940,,1,,",
        ]
    )
    parent_child_csv = "\n".join(
        [
            "id,family_tree_id,parent_id,child_id,relationship_type",
            "1,999,1,2,father",
        ]
    )

    response = client.post(
        f"/family-trees/{tree_id}/import",
        data={
            "members_csv": csv_upload(members_csv, "members.csv"),
            "parent_child_relationships_csv": csv_upload(parent_child_csv, "parent_child_relationships.csv"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "不存在的成员 id".encode() in response.data
    with app.app_context():
        assert Member.query.filter_by(name="Imported Parent").count() == 0


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


def test_uninvited_user_cannot_import_or_export(app, client):
    register(client, "alice", "Alice")
    register(client, "mallory", "Mallory")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()
        tree_id = family_tree.id

    client.post("/auth/logout")
    login(client, "mallory")

    members_csv = "\n".join(
        [
            "id,family_tree_id,name,gender,birth_year,death_year,generation,biography,created_at",
            "1,999,Imported Parent,male,1940,,1,,",
        ]
    )
    import_response = client.post(
        f"/family-trees/{tree_id}/import",
        data={"members_csv": csv_upload(members_csv, "members.csv")},
        content_type="multipart/form-data",
    )
    export_response = client.get(f"/family-trees/{tree_id}/export.zip")

    assert import_response.status_code == 403
    assert export_response.status_code == 403


def test_creator_can_delete_family_tree_with_related_data(app, client):
    register(client, "alice", "Alice")
    register(client, "bob", "Bob")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()
        bob = User.query.filter_by(username="bob").one()
        parent = Member(family_tree_id=family_tree.id, name="Parent")
        child = Member(family_tree_id=family_tree.id, name="Child")
        db.session.add_all([parent, child])
        db.session.flush()
        db.session.add(FamilyTreeCollaborator(family_tree_id=family_tree.id, user_id=bob.id))
        db.session.add(
            ParentChildRelationship(
                family_tree_id=family_tree.id,
                parent_id=parent.id,
                child_id=child.id,
                relationship_type="father",
            )
        )
        db.session.add(
            Marriage(
                family_tree_id=family_tree.id,
                person_a_id=parent.id,
                person_b_id=child.id,
            )
        )
        db.session.commit()
        tree_id = family_tree.id

    response = client.post(f"/family-trees/{tree_id}/delete")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/family-trees")
    with app.app_context():
        assert db.session.get(FamilyTree, tree_id) is None
        assert Member.query.filter_by(family_tree_id=tree_id).count() == 0
        assert FamilyTreeCollaborator.query.filter_by(family_tree_id=tree_id).count() == 0
        assert ParentChildRelationship.query.filter_by(family_tree_id=tree_id).count() == 0
        assert Marriage.query.filter_by(family_tree_id=tree_id).count() == 0


def test_non_creator_cannot_delete_family_tree(app, client):
    register(client, "alice", "Alice")
    register(client, "bob", "Bob")
    login(client, "alice")
    create_family_tree(client)

    with app.app_context():
        family_tree = FamilyTree.query.filter_by(name="Chen Genealogy").one()
        tree_id = family_tree.id

    client.post(
        f"/family-trees/{tree_id}/collaborators",
        data={"username": "bob"},
    )
    client.post("/auth/logout")
    login(client, "bob")

    response = client.post(f"/family-trees/{tree_id}/delete")

    assert response.status_code == 403
    with app.app_context():
        assert db.session.get(FamilyTree, tree_id) is not None


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
