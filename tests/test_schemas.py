import pytest
from pydantic import ValidationError
from docu_serve.schemas import UserBase, UserCreate, User

def test_user_base_valid():
    """Test creating a valid UserBase"""
    user = UserBase(
        name="John Doe",
        email="john@example.com",
        age=25
    )
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    assert user.age == 25

def test_user_base_name_too_short():
    """Test that name must be at least 2 characters"""
    with pytest.raises(ValidationError):
        UserBase(
            name="J",  # Too short
            email="j@example.com",
            age=25
        )

def test_user_base_name_too_long():
    """Test that name cannot exceed 50 characters"""
    with pytest.raises(ValidationError):
        UserBase(
            name="A" * 51,  # Too long
            email="test@example.com",
            age=25
        )

def test_user_base_invalid_email():
    """Test that email must be valid"""
    with pytest.raises(ValidationError):
        UserBase(
            name="John",
            email="notanemail",  # Invalid email
            age=25
        )

def test_user_base_age_too_young():
    """Test that age must be greater than 18"""
    with pytest.raises(ValidationError):
        UserBase(
            name="John",
            email="john@example.com",
            age=18  # Must be > 18, not >= 18
        )

def test_user_base_age_valid():
    """Test that age 19 is valid"""
    user = UserBase(
        name="John",
        email="john@example.com",
        age=19  # Just above minimum
    )
    assert user.age == 19

def test_user_create_valid():
    """Test creating a valid UserCreate"""
    user = UserCreate(
        name="Jane Doe",
        email="jane@example.com",
        age=30,
        password="Password123!"
    )
    assert user.name == "Jane Doe"
    assert user.email == "jane@example.com"
    assert user.age == 30
    assert user.password == "Password123!"

def test_user_create_password_too_short():
    """Test that password must be at least 8 characters"""
    with pytest.raises(ValidationError):
        UserCreate(
            name="Jane",
            email="jane@example.com",
            age=30,
            password="Pass1!"  # Too short but meets complexity
        )

def test_user_create_password_too_long():
    """Test that password cannot exceed 60 characters"""
    with pytest.raises(ValidationError):
        UserCreate(
            name="Jane",
            email="jane@example.com",
            age=30,
            password="A1!" + "a" * 58  # Too long but meets complexity
        )

def test_user_create_password_min_length():
    """Test password with exactly 8 characters"""
    user = UserCreate(
        name="Jane",
        email="jane@example.com",
        age=30,
        password="Pass123!"  # Exactly 8 with complexity
    )
    assert len(user.password) == 8

def test_user_create_password_max_length():
    """Test password with exactly 60 characters"""
    user = UserCreate(
        name="Jane",
        email="jane@example.com",
        age=30,
        password="A1!" + "a" * 57  # Exactly 60 with complexity
    )
    assert len(user.password) == 60

def test_password_missing_uppercase():
    """Test that password must contain an uppercase letter"""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            name="Jane",
            email="jane@example.com",
            age=30,
            password="password123!"  # No uppercase
        )
    assert "uppercase letter" in str(exc_info.value)

def test_password_missing_number():
    """Test that password must contain a number"""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            name="Jane",
            email="jane@example.com",
            age=30,
            password="Password!"  # No number
        )
    assert "number" in str(exc_info.value)

def test_password_missing_symbol():
    """Test that password must contain a symbol"""
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            name="Jane",
            email="jane@example.com",
            age=30,
            password="Password123"  # No symbol
        )
    assert "symbol" in str(exc_info.value)

def test_password_all_requirements():
    """Test that password with all requirements is valid"""
    user = UserCreate(
        name="Jane",
        email="jane@example.com",
        age=30,
        password="MyP@ssw0rd"  # Has uppercase, number, and symbol
    )
    assert user.password == "MyP@ssw0rd"

def test_user_model_complete():
    """Test the complete User model"""
    user = User(
        user_id=1,
        name="Complete User",
        email="complete@example.com",
        age=28,
        hashed_password="hashed_password_string",
        role="user"
    )
    assert user.user_id == 1
    assert user.name == "Complete User"
    assert user.email == "complete@example.com"
    assert user.age == 28
    assert user.hashed_password == "hashed_password_string"
    assert user.role == "user"

def test_user_model_admin_role():
    """Test User model with admin role"""
    admin = User(
        user_id=2,
        name="Admin",
        email="admin@test.com",
        age=35,
        hashed_password="hashed",
        role="admin"
    )
    assert admin.role == "admin"

def test_user_base_valid_email_formats():
    """Test various valid email formats"""
    valid_emails = [
        "user@example.com",
        "user.name@example.com",
        "user+tag@example.co.uk",
        "user123@test-domain.com"
    ]
    
    for email in valid_emails:
        user = UserBase(
            name="Test User",
            email=email,
            age=25
        )
        assert user.email == email

def test_user_base_invalid_email_formats():
    """Test various invalid email formats"""
    invalid_emails = [
        "notanemail",
        "@example.com",
        "user@",
        "user@.com",
        "user@domain",
        "user.com"
    ]
    
    for email in invalid_emails:
        with pytest.raises(ValidationError):
            UserBase(
                name="Test User",
                email=email,
                age=25
            )
