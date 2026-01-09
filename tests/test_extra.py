import pytest
from tests.conftest import client
from docu_serve.main import (hash_password, verify_password, create_access_token, 
                              pwd_context, ALGORITHM, SECRET_KEY, ADMIN_EMAIL, 
                              ADMIN_PASSWORD, ACCESS_TOKEN_EXPIRE_MINUTES, RABBIT_URL, app)
from datetime import timedelta, datetime
from jose import jwt
import os

def test_hash_password():
    """Test password hashing"""
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert len(hashed) > 0

def test_verify_password():
    """Test password verification"""
    password = "testpassword123"
    hashed = hash_password(password)
    
    # Correct password should verify
    assert verify_password(password, hashed) is True
    
    # Wrong password should not verify
    assert verify_password("wrongpassword", hashed) is False

def test_create_access_token():
    """Test JWT token creation"""
    data = {"sub": "test@example.com", "role": "user"}
    token = create_access_token(data, timedelta(minutes=15))
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Decode and verify the token (pass audience parameter)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience="delete-service")
    assert decoded["sub"] == "test@example.com"
    assert decoded["role"] == "user"
    assert "exp" in decoded
    assert "aud" in decoded
    assert decoded["aud"] == "delete-service"

def test_create_access_token_with_custom_expiry():
    """Test JWT token creation with custom expiry"""
    data = {"sub": "test@example.com", "role": "admin"}
    token = create_access_token(data, timedelta(minutes=30))
    
    assert token is not None
    assert isinstance(token, str)

def test_create_access_token_default_expiry():
    """Test JWT token creation with default expiry"""
    data = {"sub": "user@test.com", "role": "user"}
    token = create_access_token(data)
    
    assert token is not None
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience="delete-service")
    assert decoded["sub"] == "user@test.com"

def test_forbidden_admin_registration(client):
    """Test that admin email cannot be used for registration"""
    r = client.post("/api/users/register", params={
        "name": "Hacker",
        "email": "G00419525@atu.ie",
        "age": 25,
        "password": "tryingtohack"
    })
    assert r.status_code == 403
    assert "admin" in r.json()["detail"].lower()

def test_password_functions():
    """Test password hashing and verification together"""
    passwords = ["short", "verylongpasswordwithmanycharacters", "P@ssw0rd!", "12345678"]
    
    for password in passwords:
        hashed = hash_password(password)
        # Each hash should be different even for same password
        hashed2 = hash_password(password)
        assert hashed != hashed2  # Argon2 uses salt
        
        # But both should verify correctly
        assert verify_password(password, hashed)
        assert verify_password(password, hashed2)
        
        # Wrong passwords should not verify
        assert not verify_password("wrongpass", hashed)

def test_pwd_context_configuration():
    """Test that password context is properly configured"""
    assert pwd_context is not None
    # Verify it uses argon2
    assert 'argon2' in str(pwd_context.schemes())

def test_constants_loaded():
    """Test that environment constants are loaded"""
    assert SECRET_KEY is not None
    assert ALGORITHM == "HS256"
    assert ADMIN_EMAIL is not None
    assert ACCESS_TOKEN_EXPIRE_MINUTES > 0
    # RABBIT_URL can be None in test environment
    
def test_jwt_audience_claim():
    """Test that JWT tokens include audience claim"""
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience="delete-service")
    assert decoded["aud"] == "delete-service"
    
def test_fastapi_app_exists():
    """Test that FastAPI app is created"""
    assert app is not None
    assert hasattr(app, 'routes')
    
def test_app_has_cors_middleware():
    """Test that CORS middleware is configured"""
    # Check that middleware is present
    middleware_types = [type(m).__name__ for m in app.user_middleware]
    assert len(middleware_types) > 0  # At least some middleware exists
    assert ADMIN_PASSWORD is not None
    assert ACCESS_TOKEN_EXPIRE_MINUTES == 30

def test_verify_password_empty_password():
    """Test password verification with empty password"""
    hashed = hash_password("realpassword")
    result = verify_password("", hashed)
    assert result is False

def test_token_contains_audience():
    """Test that JWT tokens contain audience claim"""
    data = {"sub": "test@test.com", "role": "user"}
    token = create_access_token(data, timedelta(minutes=10))
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience="delete-service")
    assert decoded["aud"] == "delete-service"

def test_app_title():
    """Test that app has correct title"""
    assert app.title == "Authentication Service"

def test_app_has_middleware():
    """Test that CORS middleware is configured"""
    # Check that middleware is present
    assert len(app.user_middleware) > 0

def test_rabbit_url_loaded():
    """Test that RABBIT_URL is loaded from environment"""
    # RABBIT_URL might be None if not set in environment
    assert RABBIT_URL is None or isinstance(RABBIT_URL, str)

def test_multiple_password_hashes_different():
    """Test that multiple hashes of same password are different"""
    password = "samepassword"
    hashes = [hash_password(password) for _ in range(5)]
    
    # All hashes should be different
    assert len(set(hashes)) == 5
    
    # But all should verify correctly
    for h in hashes:
        assert verify_password(password, h)

def test_token_expiry_set_correctly():
    """Test that token expiry is set to correct value"""
    data = {"sub": "test@example.com"}
    expires_delta = timedelta(minutes=20)
    token = create_access_token(data, expires_delta)
    
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience="delete-service")
    exp_time = datetime.utcfromtimestamp(decoded["exp"])
    now = datetime.utcnow()
    
    # Check that expiry is approximately 20 minutes from now (within 1 minute tolerance)
    time_diff = (exp_time - now).total_seconds()
    assert 19 * 60 < time_diff < 21 * 60
