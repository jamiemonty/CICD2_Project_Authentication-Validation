# tests/test_users.py
import pytest

from tests.conftest import client

def user_payload(uid=1, name="Paul", email="pl@atu.ie", age=25, sid="S1234567"):
    return {"user_id": uid, "name": name, "email": email, "age": age, "student_id": sid}

def test_create_user_ok(client):
    r = client.post("/api/users", json=user_payload())
    assert r.status_code == 201
    data = r.json()
    assert data["user_id"] == 1
    assert data["name"] == "Paul"

def test_duplicate_user_id_conflict(client):
    client.post("/api/users", json=user_payload(uid=2))
    r = client.post("/api/users", json=user_payload(uid=2))
    assert r.status_code == 409 # duplicate id -> conflict
    assert "exists" in r.json()["detail"].lower()   

@pytest.mark.parametrize("bad_sid", ["BAD123", "s1234567", "S123", "S12345678"])
def test_bad_student_id_422(client, bad_sid):
    r = client.post("/api/users", json=user_payload(uid=3, sid=bad_sid))
    assert r.status_code == 422 # pydantic validation error     

def test_get_user_404(client):
    r = client.get("/api/users/999")
    assert r.status_code == 404

def test_delete_then_404(client):
    client.post("/api/users", json=user_payload(uid=10))
    r1 = client.delete("/api/users/10")
    assert r1.status_code == 204
    r2 = client.delete("/api/users/10")
    assert r2.status_code == 404

def test_put_user_success(client):
    # First create a user
    client.post("/api/users", json=user_payload(uid=5))
    
    # Update the user with new data
    updated_data = user_payload(uid=5, name="Updated Paul")
    r = client.put("/api/users/5", json=updated_data)
    
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == 5
    assert data["name"] == "Updated Paul"

def test_put_user_not_found(client):
    # Try to update a user that doesn't exist
    updated_data = user_payload(uid=999)
    r = client.put("/api/users/999", json=updated_data)
    
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()

@pytest.mark.parametrize("bad_email", ["bademail", "user@.com", "user@com", "@domain.com", "user@domain", "user.com"])
def test_bad_email_422_on_create(client, bad_email):
    r = client.post("/api/users", json=user_payload(uid=20, email=bad_email))
    assert r.status_code == 422 # pydantic validation error     
    assert "value is not a valid email address" in r.json()["detail"][0]["msg"]