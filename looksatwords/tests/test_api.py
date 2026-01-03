"""Tests for FastAPI backend integration."""
import json
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from looksatwords.app.main import app
from looksatwords.app.database import get_session


@pytest.fixture(name="session")
def session_fixture():
    """Create test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from looksatwords.app.models import SQLModel
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with test database."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_analyze_conversation(client: TestClient):
    """Test conversation analysis endpoint."""
    text = "Alice: Hello Bob. Bob: Hi Alice, how are you? Alice: Great! Bob: That's wonderful."
    request_data = {
        "text": text,
        "title": "Test Conversation"
    }
    
    response = client.post(
        "/api/conversations/analyze",
        json=request_data
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["title"] == "Test Conversation"
    assert "threads" in data
    assert "tangents" in data


def test_list_conversations(client: TestClient):
    """Test list conversations endpoint."""
    # Add a conversation first
    text = "Alice: Hello Bob. Bob: Hi Alice."
    request_data = {
        "text": text,
        "title": "Test Conversation 1"
    }
    client.post("/api/conversations/analyze", json=request_data)
    
    # List conversations
    response = client.get("/api/conversations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_conversation(client: TestClient):
    """Test get conversation endpoint."""
    # Add a conversation first
    text = "Alice: Hello Bob. Bob: Hi Alice."
    request_data = {
        "text": text,
        "title": "Test Conversation"
    }
    create_response = client.post("/api/conversations/analyze", json=request_data)
    conversation_id = create_response.json()["conversation_id"]
    
    # Get conversation
    response = client.get(f"/api/conversations/{conversation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conversation_id
    assert data["title"] == "Test Conversation"


def test_delete_conversation(client: TestClient):
    """Test delete conversation endpoint."""
    # Add a conversation first
    text = "Alice: Hello Bob. Bob: Hi Alice."
    request_data = {
        "text": text,
        "title": "Test Conversation"
    }
    create_response = client.post("/api/conversations/analyze", json=request_data)
    conversation_id = create_response.json()["conversation_id"]
    
    # Delete conversation
    delete_response = client.delete(f"/api/conversations/{conversation_id}")
    assert delete_response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f"/api/conversations/{conversation_id}")
    assert get_response.status_code == 404
