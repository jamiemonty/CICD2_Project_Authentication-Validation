import pytest

from tests.conftest import client


def user_payload(uid=200, name="Alice", email="alice@example.com", age=30, username="alice1", password="passw0rd"):
    return {"user_id": uid, "name": name, "email": email, "age": age, "username": username, "password": password}


def test_get_users_list(client):
    # ensure list endpoint returns created users
    client.post("/api/users", json=user_payload(uid=201))
    r = client.get("/api/users")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(u["user_id"] == 201 for u in data)


def test_get_user_success(client):
    client.post("/api/users", json=user_payload(uid=202, name="Bob"))
    r = client.get("/api/users/202")
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == 202
    assert data["name"] == "Bob"


def test_login_success_and_failure(client):
    # create user and login successfully
    client.post("/api/users", json=user_payload(uid=203, username="loginuser", password="s3cret"))
    r = client.post("/api/login", json={"username": "loginuser", "password": "s3cret"})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["user_id"] == 203

    # failed login
    r2 = client.post("/api/login", json={"username": "loginuser", "password": "wrong"})
    assert r2.status_code == 401
