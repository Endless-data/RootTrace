from app import create_app


def test_create_app():
    app = create_app({"TESTING": True})

    assert app.testing


def test_index_route():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json() == {"name": "RootTrace", "status": "ok"}
