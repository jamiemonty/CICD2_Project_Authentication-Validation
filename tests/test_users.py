# tests/test_users.py
import pytest
from tests.conftest import client

def test_register_user_success(client):
    """Test successful user registration"""
    r = client.post("/api/users/register", params={
        "name": "John Doe",
        "email": "john@example.com",
        "age": 25,
        "password": "password123"
    })
    assert r.status_code == 201
    data = r.json()
    assert "user_id" in data
    assert data["msg"] == "User registered successfully"

def test_register_duplicate_email(client):
    """Test that duplicate email returns conflict"""
    client.post("/api/users/register", params={
        "name": "Jane Doe",
        "email": "jane@example.com",
        "age": 30,
        "password": "password123"
    })
    r = client.post("/api/users/register", params={
        "name": "Jane Smith",
        "email": "jane@example.com",
        "age": 28,
        "password": "password456"
    })
    assert r.status_code == 409
    assert "exists" in r.json()["detail"].lower()

def test_register_as_admin_forbidden(client):
    """Test that registering with admin email is forbidden"""
    r = client.post("/api/users/register", params={
        "name": "Admin User",
        "email": "G00419525@atu.ie",
        "age": 30,
        "password": "password123"
    })
    assert r.status_code == 403
    assert "admin" in r.json()["detail"].lower()

def test_login_success(client):
    """Test successful login"""
    # Register user first
    client.post("/api/users/register", params={
        "name": "Login Test",
        "email": "logintest@example.com",
        "age": 25,
        "password": "testpass123"
    })
    
    # Now login
    r = client.post("/api/users/login", data={
        "username": "logintest@example.com",
        "password": "testpass123"
    })
    assert r.status_code == 202
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    """Test login with wrong password"""
    # Register user first
    client.post("/api/users/register", params={
        "name": "Wrong Pass",
        "email": "wrongpass@example.com",
        "age": 25,
        "password": "correctpass"
    })
    
    # Try wrong password
    r = client.post("/api/users/login", data={
        "username": "wrongpass@example.com",
        "password": "wrongpassword"
    })
    assert r.status_code == 401
    assert "credentials" in r.json()["detail"].lower()

def test_login_nonexistent_user(client):
    """Test login with user that doesn't exist"""
    r = client.post("/api/users/login", data={
        "username": "nonexistent@example.com",
        "password": "anypassword"
    })
    assert r.status_code == 401

def test_admin_login(client):
    """Test that admin user can login"""
    r = client.post("/api/users/login", data={
        "username": "G00419525@atu.ie",
        "password": "password"
    })
    assert r.status_code == 202
    data = r.json()
    assert "access_token" in data

def test_register_multiple_users(client):
    """Test registering multiple different users"""
    users = [
        {"name": "User1", "email": "user1@test.com", "age": 25, "password": "pass1234"},
        {"name": "User2", "email": "user2@test.com", "age": 30, "password": "pass5678"},
        {"name": "User3", "email": "user3@test.com", "age": 35, "password": "pass9012"},
    ]
    
    for user in users:
        r = client.post("/api/users/register", params=user)
        assert r.status_code == 201
        data = r.json()
        assert "user_id" in data