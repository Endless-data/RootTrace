import pytest
from werkzeug.security import check_password_hash

from app import create_app
from app.extensions import db
from app.models import User


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


def register(client, username="alice", display_name="Alice", password="secret"):
    return client.post(
        "/auth/register",
        data={
            "username": username,
            "display_name": display_name,
            "password": password,
        },
    )


def login(client, username="alice", password="secret"):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )


def test_register_creates_user_with_hashed_password(app, client):
    response = register(client)

    assert response.status_code == 302
    with app.app_context():
        user = User.query.filter_by(username="alice").one()
        assert user.display_name == "Alice"
        assert user.password_hash != "secret"
        assert check_password_hash(user.password_hash, "secret")


def test_register_requires_unique_username(client):
    register(client)

    response = register(client, display_name="Another Alice")

    assert response.status_code == 400
    assert b"already registered" in response.data


@pytest.mark.parametrize(
    ("field", "message"),
    (
        ("username", b"Username is required"),
        ("display_name", b"Display name is required"),
        ("password", b"Password is required"),
    ),
)
def test_register_validates_required_fields(client, field, message):
    data = {
        "username": "alice",
        "display_name": "Alice",
        "password": "secret",
    }
    data[field] = ""

    response = client.post("/auth/register", data=data)

    assert response.status_code == 400
    assert message in response.data


def test_login_sets_session(client):
    register(client)

    response = login(client)

    assert response.status_code == 302
    with client.session_transaction() as session_data:
        assert session_data["user_id"] == 1


def test_login_rejects_invalid_credentials(client):
    register(client)

    response = login(client, password="wrong")

    assert response.status_code == 401
    assert b"Invalid username or password" in response.data
    with client.session_transaction() as session_data:
        assert "user_id" not in session_data


def test_logout_clears_session(client):
    register(client)
    login(client)

    response = client.post("/auth/logout")

    assert response.status_code == 302
    with client.session_transaction() as session_data:
        assert "user_id" not in session_data
