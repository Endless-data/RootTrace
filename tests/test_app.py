from app import create_app


def test_create_app():
    app = create_app({"TESTING": True})

    assert app.testing


def test_index_route():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
    assert "RootTrace 族谱管理系统".encode() in response.data
    assert "创建账户".encode() in response.data
    assert b'class="button button-secondary" href="/auth/login"' in response.data
