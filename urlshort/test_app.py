import pytest

from app import create_app, is_valid_url
from shortener import decode, encode


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client()


def test_base62_roundtrip():
    for n in (0, 1, 61, 62, 12345, 10**12):
        assert decode(encode(n)) == n


def test_url_validation():
    assert is_valid_url("https://example.com/a?b=1")
    assert not is_valid_url("javascript:alert(1)")
    assert not is_valid_url("ftp://example.com")
    assert not is_valid_url("not a url")
    assert not is_valid_url("")


def test_shorten_and_redirect(client):
    res = client.post("/api/shorten", json={"url": "https://example.com/page"})
    assert res.status_code == 201
    code = res.get_json()["code"]

    redirect = client.get(f"/{code}")
    assert redirect.status_code == 302
    assert redirect.headers["Location"] == "https://example.com/page"


def test_click_stats(client):
    code = client.post("/api/shorten", json={"url": "https://example.com"}).get_json()["code"]
    client.get(f"/{code}")
    client.get(f"/{code}")
    stats = client.get(f"/api/stats/{code}").get_json()
    assert stats["clicks"] == 2
    assert stats["last_clicked"] is not None


def test_custom_code_and_conflict(client):
    ok = client.post("/api/shorten", json={"url": "https://a.com", "code": "my-link"})
    assert ok.status_code == 201
    assert ok.get_json()["code"] == "my-link"

    dup = client.post("/api/shorten", json={"url": "https://b.com", "code": "my-link"})
    assert dup.status_code == 409


def test_rejects_bad_input(client):
    assert client.post("/api/shorten", json={"url": "nope"}).status_code == 400
    assert client.post("/api/shorten", json={"url": "https://a.com", "code": "x"}).status_code == 400
    assert client.post("/api/shorten", json={"url": "https://a.com", "code": "api"}).status_code == 400


def test_unknown_code_404(client):
    assert client.get("/doesnotexist").status_code == 404
    assert client.get("/api/stats/doesnotexist").status_code == 404
