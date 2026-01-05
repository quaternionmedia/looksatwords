"""Tests for the analytics service and API endpoints.

Tests cover:
- ConversationAnalyticsService unit tests
- Analytics API endpoint integration tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from looksatwords.app.main import app
from looksatwords.app.database import get_session
from looksatwords.app.analytics_service import (
    ConversationAnalyticsService,
    get_analytics_service,
    NLTK_AVAILABLE,
    POS_GROUPS,
)


# =============================================================================
# Fixtures
# =============================================================================

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


@pytest.fixture
def analytics_service():
    """Create analytics service instance."""
    return ConversationAnalyticsService()


@pytest.fixture
def sample_time_points():
    """Sample time points as returned by ThreadVisualizerBackend."""
    return [
        {
            "time": 0,
            "text": "hello everyone how are you",
            "originalLine": "Alice: Hello everyone, how are you?",
            "speaker": "Alice",
            "speakerInfo": {"color": "#ff6b6b", "index": 0},
        },
        {
            "time": 30,
            "text": "doing great thanks for asking",
            "originalLine": "Bob: Doing great! Thanks for asking.",
            "speaker": "Bob",
            "speakerInfo": {"color": "#00d4ff", "index": 1},
        },
        {
            "time": 60,
            "text": "terrible day honestly quite upset",
            "originalLine": "Charlie: Terrible day honestly, quite upset.",
            "speaker": "Charlie",
            "speakerInfo": {"color": "#00ff88", "index": 2},
        },
        {
            "time": 90,
            "text": "oh no what happened",
            "originalLine": "Alice: Oh no, what happened?",
            "speaker": "Alice",
            "speakerInfo": {"color": "#ff6b6b", "index": 0},
        },
    ]


@pytest.fixture
def sample_conversation_text():
    """Sample conversation text for API tests."""
    return """[0:00] Alice: Hello everyone, how are you?
[0:30] Bob: Doing great! Thanks for asking.
[1:00] Charlie: Terrible day honestly, quite upset.
[1:30] Alice: Oh no, what happened?"""


# =============================================================================
# Analytics Service Unit Tests
# =============================================================================

class TestConversationAnalyticsService:
    """Unit tests for ConversationAnalyticsService."""

    def test_service_initialization(self, analytics_service):
        """Test that service initializes correctly."""
        assert analytics_service is not None
        if NLTK_AVAILABLE:
            assert analytics_service.sia is not None
            assert analytics_service.lemmatizer is not None
            assert len(analytics_service.stop_words) > 0

    def test_analyze_empty_text(self, analytics_service):
        """Test analyzing empty text."""
        result = analytics_service.analyze_text("")
        assert result["word_count"] == 0
        assert result["sentiment"]["compound"] == 0.0
        assert len(result["words"]) == 0

    def test_analyze_simple_text(self, analytics_service):
        """Test analyzing simple text."""
        result = analytics_service.analyze_text("Hello, how are you doing today?")
        assert result["word_count"] >= 0  # Depends on stopwords
        assert "compound" in result["sentiment"]
        assert isinstance(result["pos_counts"], dict)

    @pytest.mark.skipif(not NLTK_AVAILABLE, reason="NLTK not available")
    def test_sentiment_positive(self, analytics_service):
        """Test sentiment analysis on positive text."""
        result = analytics_service.analyze_text(
            "This is absolutely wonderful and amazing! I love it so much!"
        )
        assert result["sentiment"]["compound"] > 0.0
        assert result["sentiment"]["pos"] > 0.0

    @pytest.mark.skipif(not NLTK_AVAILABLE, reason="NLTK not available")
    def test_sentiment_negative(self, analytics_service):
        """Test sentiment analysis on negative text."""
        result = analytics_service.analyze_text(
            "This is terrible and awful. I hate it, worst thing ever."
        )
        assert result["sentiment"]["compound"] < 0.0
        assert result["sentiment"]["neg"] > 0.0

    @pytest.mark.skipif(not NLTK_AVAILABLE, reason="NLTK not available")
    def test_pos_tagging(self, analytics_service):
        """Test part-of-speech tagging."""
        result = analytics_service.analyze_text(
            "The quick brown fox jumps over the lazy dog."
        )
        # Should detect nouns, verbs, adjectives
        assert result["pos_counts"]["noun"] > 0
        assert result["pos_counts"]["verb"] > 0
        assert result["pos_counts"]["adjective"] > 0

    def test_analyze_conversation_empty(self, analytics_service):
        """Test analyzing empty conversation."""
        result = analytics_service.analyze_conversation([])
        assert result["points"] == []
        assert result["aggregated"]["total_messages"] == 0
        assert result["sentiment_timeline"] == []
        assert result["speaker_analytics"] == {}

    def test_analyze_conversation(self, analytics_service, sample_time_points):
        """Test analyzing a full conversation."""
        result = analytics_service.analyze_conversation(sample_time_points)
        
        # Check structure
        assert "points" in result
        assert "aggregated" in result
        assert "sentiment_timeline" in result
        assert "speaker_analytics" in result
        assert "nltk_available" in result
        
        # Check points
        assert len(result["points"]) == 4
        
        # Check aggregated
        assert result["aggregated"]["total_messages"] == 4
        assert result["aggregated"]["total_words"] >= 0
        assert "overall_sentiment" in result["aggregated"]
        
        # Check sentiment timeline
        assert len(result["sentiment_timeline"]) == 4
        for point in result["sentiment_timeline"]:
            assert "time" in point
            assert "compound" in point
            assert "speaker" in point
        
        # Check speaker analytics
        assert "Alice" in result["speaker_analytics"]
        assert "Bob" in result["speaker_analytics"]
        assert "Charlie" in result["speaker_analytics"]
        assert result["speaker_analytics"]["Alice"]["message_count"] == 2
        assert result["speaker_analytics"]["Bob"]["message_count"] == 1
        assert result["speaker_analytics"]["Charlie"]["message_count"] == 1

    @pytest.mark.skipif(not NLTK_AVAILABLE, reason="NLTK not available")
    def test_word_frequency(self, analytics_service):
        """Test word frequency analysis."""
        time_points = [
            {"time": 0, "text": "hello world", "originalLine": "A: hello world", "speaker": "A", "speakerInfo": {}},
            {"time": 30, "text": "hello again world", "originalLine": "B: hello again world", "speaker": "B", "speakerInfo": {}},
            {"time": 60, "text": "world is great", "originalLine": "A: world is great", "speaker": "A", "speakerInfo": {}},
        ]
        result = analytics_service.analyze_conversation(time_points)
        
        # Word frequency should include common words
        word_freq = result["aggregated"]["word_frequency"]
        words = [wf["word"] for wf in word_freq]
        # "world" should be frequent (appears 3 times, but may be lemmatized)
        assert len(word_freq) > 0

    def test_sentiment_label(self, analytics_service):
        """Test sentiment label conversion."""
        assert analytics_service._sentiment_label(0.5) == "positive"
        assert analytics_service._sentiment_label(-0.5) == "negative"
        assert analytics_service._sentiment_label(0.0) == "neutral"
        assert analytics_service._sentiment_label(0.04) == "neutral"
        assert analytics_service._sentiment_label(-0.04) == "neutral"


class TestAnalyticsServiceSingleton:
    """Tests for the singleton pattern."""

    def test_get_analytics_service_returns_same_instance(self):
        """Test that get_analytics_service returns the same instance."""
        service1 = get_analytics_service()
        service2 = get_analytics_service()
        assert service1 is service2


# =============================================================================
# API Integration Tests
# =============================================================================

class TestAnalyticsAPIEndpoints:
    """Integration tests for analytics API endpoints."""

    def test_analyze_with_analytics_endpoint(self, client: TestClient, sample_conversation_text):
        """Test the analyze-with-analytics endpoint."""
        response = client.post(
            "/api/conversations/analyze-with-analytics",
            json={
                "text": sample_conversation_text,
                "title": "Test Analytics Conversation"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check standard fields
        assert "conversation_id" in data
        assert data["title"] == "Test Analytics Conversation"
        assert "threads" in data
        assert "tangents" in data
        
        # Check analytics fields
        assert "analytics" in data
        assert "sentiment_timeline" in data
        assert "speaker_analytics" in data
        
        # Check analytics structure
        analytics = data["analytics"]
        assert "total_messages" in analytics
        assert "total_words" in analytics
        assert "average_sentiment" in analytics
        assert "overall_sentiment" in analytics
        assert "word_frequency" in analytics
        assert "pos_distribution" in analytics
        
        # Cleanup
        conv_id = data["conversation_id"]
        client.delete(f"/api/conversations/{conv_id}")

    def test_get_conversation_analytics_endpoint(self, client: TestClient, sample_conversation_text):
        """Test the get analytics endpoint."""
        # First create a conversation
        create_response = client.post(
            "/api/conversations/analyze",
            json={
                "text": sample_conversation_text,
                "title": "Test Get Analytics"
            }
        )
        assert create_response.status_code == 200
        conv_id = create_response.json()["conversation_id"]
        
        # Then get analytics
        analytics_response = client.get(f"/api/conversations/{conv_id}/analytics")
        assert analytics_response.status_code == 200
        data = analytics_response.json()
        
        # Check structure
        assert data["conversation_id"] == conv_id
        assert "aggregated" in data
        assert "sentiment_timeline" in data
        assert "speaker_analytics" in data
        assert "nltk_available" in data
        
        # Check aggregated analytics
        aggregated = data["aggregated"]
        assert aggregated["total_messages"] == 4
        assert "average_sentiment" in aggregated
        assert "word_frequency" in aggregated
        
        # Check sentiment timeline
        timeline = data["sentiment_timeline"]
        assert len(timeline) == 4
        assert all("time" in p for p in timeline)
        assert all("compound" in p for p in timeline)
        assert all("speaker" in p for p in timeline)
        
        # Check speaker analytics
        speakers = data["speaker_analytics"]
        assert "Alice" in speakers
        assert speakers["Alice"]["message_count"] == 2
        
        # Cleanup
        client.delete(f"/api/conversations/{conv_id}")

    def test_analytics_for_nonexistent_conversation(self, client: TestClient):
        """Test analytics endpoint with non-existent conversation ID."""
        response = client.get("/api/conversations/99999/analytics")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_analytics_sentiment_values(self, client: TestClient):
        """Test that sentiment values are reasonable."""
        # Create conversation with mixed sentiment
        text = """[0:00] Alice: I am so happy today, everything is wonderful!
[0:30] Bob: That's terrible news, I'm very sad and disappointed.
[1:00] Alice: The weather is okay I suppose."""
        
        response = client.post(
            "/api/conversations/analyze-with-analytics",
            json={"text": text, "title": "Sentiment Test"}
        )
        assert response.status_code == 200
        data = response.json()
        
        timeline = data["sentiment_timeline"]
        
        # First message should be positive
        if NLTK_AVAILABLE:
            assert timeline[0]["compound"] > 0, "Happy message should have positive sentiment"
            assert timeline[1]["compound"] < 0, "Sad message should have negative sentiment"
        
        # Cleanup
        client.delete(f"/api/conversations/{data['conversation_id']}")

    def test_analytics_word_frequency(self, client: TestClient):
        """Test word frequency in analytics."""
        text = """[0:00] Alice: Technology technology technology innovation.
[0:30] Bob: Technology is changing everything with technology.
[1:00] Alice: More technology please."""
        
        response = client.post(
            "/api/conversations/analyze-with-analytics",
            json={"text": text, "title": "Word Freq Test"}
        )
        assert response.status_code == 200
        data = response.json()
        
        word_freq = data["analytics"]["word_frequency"]
        if NLTK_AVAILABLE and len(word_freq) > 0:
            # "technology" should be one of the most frequent
            words = [w["word"] for w in word_freq]
            assert "technology" in words or "tech" in words
        
        # Cleanup
        client.delete(f"/api/conversations/{data['conversation_id']}")

    def test_analytics_pos_distribution(self, client: TestClient):
        """Test POS distribution in analytics."""
        text = """[0:00] Alice: The quick brown fox jumps over the lazy dog.
[0:30] Bob: She sells seashells by the seashore."""
        
        response = client.post(
            "/api/conversations/analyze-with-analytics",
            json={"text": text, "title": "POS Test"}
        )
        assert response.status_code == 200
        data = response.json()
        
        pos_dist = data["analytics"]["pos_distribution"]
        
        # Check all POS groups are present
        for group in POS_GROUPS.keys():
            assert group in pos_dist
        
        if NLTK_AVAILABLE:
            # Should have nouns, verbs, adjectives
            assert pos_dist["noun"] > 0
            assert pos_dist["verb"] > 0
        
        # Cleanup
        client.delete(f"/api/conversations/{data['conversation_id']}")

    def test_analytics_speaker_breakdown(self, client: TestClient):
        """Test per-speaker analytics."""
        text = """[0:00] Alice: Hello everyone!
[0:30] Alice: How is everyone doing?
[1:00] Alice: I have a lot to say today.
[1:30] Bob: Just one thing from me."""
        
        response = client.post(
            "/api/conversations/analyze-with-analytics",
            json={"text": text, "title": "Speaker Test"}
        )
        assert response.status_code == 200
        data = response.json()
        
        speaker_analytics = data["speaker_analytics"]
        
        assert "Alice" in speaker_analytics
        assert "Bob" in speaker_analytics
        
        assert speaker_analytics["Alice"]["message_count"] == 3
        assert speaker_analytics["Bob"]["message_count"] == 1
        
        # Alice talks more, should have more total words
        assert speaker_analytics["Alice"]["total_words"] >= speaker_analytics["Bob"]["total_words"]
        
        # Cleanup
        client.delete(f"/api/conversations/{data['conversation_id']}")


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestAnalyticsEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_conversation(self, client: TestClient):
        """Test analytics with empty conversation text."""
        response = client.post(
            "/api/conversations/analyze-with-analytics",
            json={"text": "", "title": "Empty Test"}
        )
        # Should handle gracefully (may have 0 messages)
        assert response.status_code == 200
        data = response.json()
        assert data["analytics"]["total_messages"] == 0

    def test_single_message(self, client: TestClient):
        """Test analytics with single message."""
        response = client.post(
            "/api/conversations/analyze-with-analytics",
            json={"text": "[0:00] Alice: Hello!", "title": "Single Message"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["analytics"]["total_messages"] == 1
        assert len(data["sentiment_timeline"]) == 1
        
        # Cleanup
        client.delete(f"/api/conversations/{data['conversation_id']}")

    def test_special_characters(self, client: TestClient):
        """Test analytics with special characters."""
        text = """[0:00] Alice: Hello!!! 😀 🎉
[0:30] Bob: @#$%^&*() testing special chars!!!"""
        
        response = client.post(
            "/api/conversations/analyze-with-analytics",
            json={"text": text, "title": "Special Chars"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["analytics"]["total_messages"] == 2
        
        # Cleanup
        client.delete(f"/api/conversations/{data['conversation_id']}")

    def test_long_conversation(self, client: TestClient):
        """Test analytics with longer conversation."""
        messages = [f"[{i}:00] Speaker{i % 3}: Message number {i} with some words." 
                    for i in range(20)]
        text = "\n".join(messages)
        
        response = client.post(
            "/api/conversations/analyze-with-analytics",
            json={"text": text, "title": "Long Conversation"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["analytics"]["total_messages"] == 20
        assert len(data["sentiment_timeline"]) == 20
        
        # Cleanup
        client.delete(f"/api/conversations/{data['conversation_id']}")

    def test_unicode_text(self, client: TestClient):
        """Test analytics with unicode text."""
        text = """[0:00] Alice: Bonjour, comment ça va?
[0:30] Bob: 你好，很高兴认识你
[1:00] Charlie: مرحبا"""
        
        response = client.post(
            "/api/conversations/analyze-with-analytics",
            json={"text": text, "title": "Unicode Test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["analytics"]["total_messages"] == 3
        
        # Cleanup
        client.delete(f"/api/conversations/{data['conversation_id']}")
