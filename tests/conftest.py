import pytest

from fastapi.testclient import TestClient

from docu_serve.main import app


@pytest.fixture
def client():
    return TestClient(app)
