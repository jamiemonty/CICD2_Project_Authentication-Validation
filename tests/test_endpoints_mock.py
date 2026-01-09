"""Test endpoints with mocked database"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from docu_serve.main import app, hash_password
from docu_serve.models import User

client = TestClient(app)

def test_register_user_forbidden_admin():
    """Test that admin email is forbidden for registration"""
    response = client.post("/api/users/register", params={
        "name": "Hacker",
        "email": "G00419525@atu.ie",
        "age": 25,
        "password": "Password123!"
    })
    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()

@patch('docu_serve.main.publish_event')
def test_register_user_success(mock_publish):
    """Test successful user registration"""
    from docu_serve.database import get_db as real_get_db
    from docu_serve.main import app
    
    def mock_db_gen():
        mock_db = MagicMock()
        # Mock query to return None (user doesn't exist)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock the database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda x: setattr(x, 'user_id', 1))
        yield mock_db
    
    app.dependency_overrides[real_get_db] = mock_db_gen
    
    response = client.post("/api/users/register", params={
        "name": "Test User",
        "email": "test@example.com",
        "age": 25,
        "password": "Password123!"
    })
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 201
    assert "user_id" in response.json()

def test_register_duplicate_email():
    """Test registration with duplicate email"""
    # We need to properly mock the dependency injection
    from docu_serve.database import get_db as real_get_db
    
    def mock_db_gen():
        mock_db = MagicMock()
        # Mock query to return existing user
        existing_user = User(user_id=1, name="Existing", email="existing@example.com",
                            age=25, hashed_password="hash", role="user")
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        yield mock_db
    
    # Override the dependency
    from docu_serve.main import app
    app.dependency_overrides[real_get_db] = mock_db_gen
    
    response = client.post("/api/users/register", params={
        "name": "New User",
        "email": "existing@example.com",
        "age": 30,
        "password": "Password123!"
    })
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

def test_login_success():
    """Test successful login"""
    from docu_serve.database import get_db as real_get_db
    from docu_serve.main import app
    
    def mock_db_gen():
        mock_db = MagicMock()
        # Create a mock user with hashed password
        hashed_pw = hash_password("Correct123!")
        mock_user = User(user_id=1, name="Test", email="test@example.com",
                        age=25, hashed_password=hashed_pw, role="user")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        yield mock_db
    
    app.dependency_overrides[real_get_db] = mock_db_gen
    
    response = client.post("/api/users/login", data={
        "username": "test@example.com",
        "password": "Correct123!"
    })
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 202
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_password():
    """Test login with wrong password"""
    from docu_serve.database import get_db as real_get_db
    from docu_serve.main import app
    
    def mock_db_gen():
        mock_db = MagicMock()
        # Create a mock user
        hashed_pw = hash_password("Correct123!")
        mock_user = User(user_id=1, name="Test", email="test@example.com",
                        age=25, hashed_password=hashed_pw, role="user")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        yield mock_db
    
    app.dependency_overrides[real_get_db] = mock_db_gen
    
    response = client.post("/api/users/login", data={
        "username": "test@example.com",
        "password": "Wrong123!"
    })
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_login_nonexistent_user():
    """Test login with user that doesn't exist"""
    from docu_serve.database import get_db as real_get_db
    from docu_serve.main import app
    
    def mock_db_gen():
        mock_db = MagicMock()
        # Mock query to return None (user doesn't exist)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        yield mock_db
    
    app.dependency_overrides[real_get_db] = mock_db_gen
    
    response = client.post("/api/users/login", data={
        "username": "nonexistent@example.com",
        "password": "AnyPass1!"
    })
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
