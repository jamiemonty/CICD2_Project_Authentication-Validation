"""Tests for health check endpoints"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from docu_serve.main import app


def test_health_check_basic(client: TestClient):
    """Test basic health check endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "authentication-service"
    assert "timestamp" in data


def test_liveness_check(client: TestClient):
    """Test liveness check endpoint returns 200"""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_check_success(client: TestClient):
    """Test readiness check with healthy database"""
    # Use a fresh client without dependency overrides to test real database
    from docu_serve.main import get_db
    
    # Clear overrides temporarily to use actual test database
    app.dependency_overrides.clear()
    
    def override_get_db():
        from tests.conftest import TestingSessionLocal
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        response = test_client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "healthy"
        assert "timestamp" in data


def test_readiness_check_db_failure(client: TestClient):
    """Test readiness check with database failure"""
    from docu_serve.main import get_db
    
    def mock_db_failure():
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Database connection lost")
        yield mock_db
    
    app.dependency_overrides[get_db] = mock_db_failure
    
    try:
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert "Database connection lost" in data["detail"]["database"]
    finally:
        app.dependency_overrides.clear()


def test_rabbitmq_health_not_configured(client: TestClient):
    """Test RabbitMQ health when RABBIT_URL is not set"""
    with patch("docu_serve.main.RABBIT_URL", None):
        response = client.get("/health/rabbitmq")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_configured"
        assert data["configured"] is False


def test_rabbitmq_health_circuit_open(client: TestClient):
    """Test RabbitMQ health when circuit breaker is OPEN"""
    from docu_serve.main import rabbitmq_circuit_breaker
    
    # Save original state
    original_state = rabbitmq_circuit_breaker.state
    original_failures = rabbitmq_circuit_breaker.failure_count
    
    try:
        rabbitmq_circuit_breaker.state = "OPEN"
        rabbitmq_circuit_breaker.failure_count = 5
        
        response = client.get("/health/rabbitmq")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["circuit_breaker_state"] == "OPEN"
        assert "Circuit breaker is OPEN" in data["message"]
    finally:
        # Restore original state
        rabbitmq_circuit_breaker.state = original_state
        rabbitmq_circuit_breaker.failure_count = original_failures


@patch("docu_serve.main._publish_to_rabbitmq", new_callable=AsyncMock)
def test_rabbitmq_health_success(mock_publish, client: TestClient):
    """Test RabbitMQ health with successful connection"""
    from docu_serve.main import rabbitmq_circuit_breaker
    
    # Ensure circuit is closed
    rabbitmq_circuit_breaker.state = "CLOSED"
    rabbitmq_circuit_breaker.failure_count = 0
    
    # Mock successful publish
    mock_publish.return_value = None
    
    with patch("docu_serve.main.RABBIT_URL", "amqp://localhost"):
        response = client.get("/health/rabbitmq")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["circuit_breaker_state"] == "CLOSED"
        assert "Connection successful" in data["message"]


@patch("docu_serve.main._publish_to_rabbitmq", new_callable=AsyncMock)
def test_rabbitmq_health_connection_failure(mock_publish, client: TestClient):
    """Test RabbitMQ health with connection failure"""
    from docu_serve.main import rabbitmq_circuit_breaker
    
    # Ensure circuit is closed
    rabbitmq_circuit_breaker.state = "CLOSED"
    
    # Mock failed publish
    mock_publish.side_effect = Exception("Connection refused")
    
    with patch("docu_serve.main.RABBIT_URL", "amqp://localhost"):
        response = client.get("/health/rabbitmq")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "Connection refused" in data["message"]
