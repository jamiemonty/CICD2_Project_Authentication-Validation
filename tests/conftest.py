import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from docu_serve.main import app, hash_password
from docu_serve.database import get_db
from docu_serve.models import Base, User
import os
import tempfile

# Use a file-based SQLite database for tests to avoid in-memory threading issues
test_db_fd, test_db_path = tempfile.mkstemp(suffix=".db")

engine = create_engine(
    f"sqlite:///{test_db_path}",
    connect_args={"check_same_thread": False},
)
 
@event.listens_for(engine, "connect")
def _fk_on(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")
 
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
 
 
@pytest.fixture(autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    
    # Create admin user for testing
    db = TestingSessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "G00419525@atu.ie")
        admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!")  # Default meets complexity
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            hashed_pw = hash_password(admin_password)
            admin_user = User(
                name="System Admin",
                email=admin_email,
                age=22,
                hashed_password=hashed_pw,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)
 
 
@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
 
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def pytest_sessionfinish(session, exitstatus):
    """Cleanup temp database after all tests complete"""
    try:
        os.close(test_db_fd)
        os.unlink(test_db_path)
    except:
        pass