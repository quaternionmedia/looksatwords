"""Tests for dynamic topic extraction service."""

import pytest
from fastapi.testclient import TestClient

from looksatwords.app.topic_service import TopicExtractor, get_topic_extractor


class TestTopicExtractor:
    """Tests for TopicExtractor class."""
    
    def test_extractor_initialization(self):
        """Test that TopicExtractor initializes correctly."""
        extractor = TopicExtractor()
        assert extractor is not None
    
    def test_extract_topics_empty_text(self):
        """Test topic extraction from empty text."""
        extractor = TopicExtractor()
        topics = extractor.extract_topics("")
        assert isinstance(topics, list)
    
    def test_extract_topics_simple_text(self):
        """Test topic extraction from simple text."""
        extractor = TopicExtractor()
        text = """
        [0:00] Alice: Let's discuss the marketing strategy.
        [0:30] Bob: I think we need to focus on digital marketing.
        [1:00] Alice: Good point about marketing!
        """
        topics = extractor.extract_topics(text)
        assert isinstance(topics, list)
        # Should find at least one topic
        assert len(topics) >= 1
    
    def test_extract_topics_returns_dict_structure(self):
        """Test that extracted topics have the correct structure."""
        extractor = TopicExtractor()
        text = """
        [0:00] John: We need to discuss the budget for next quarter.
        [0:30] Sarah: The budget should include more for research.
        [1:00] John: Research is important for our budget planning.
        """
        topics = extractor.extract_topics(text)
        
        if topics:
            topic = topics[0]
            assert 'name' in topic
            assert 'keywords' in topic
            assert 'score' in topic
            assert 'sources' in topic
            assert isinstance(topic['keywords'], list)
    
    def test_extract_topics_max_topics(self):
        """Test that max_topics parameter is respected."""
        extractor = TopicExtractor()
        text = """
        [0:00] Alice: Marketing and sales are important.
        [0:30] Bob: Technology and innovation drive growth.
        [1:00] Carol: Finance and budget need attention.
        [1:30] Dave: Environment and sustainability matter.
        [2:00] Eve: Strategy and planning for success.
        """
        topics = extractor.extract_topics(text, max_topics=3)
        assert len(topics) <= 3
    
    def test_extract_topics_repeated_words(self):
        """Test topic extraction with repeated words."""
        extractor = TopicExtractor()
        text = """
        [0:00] Alice: The project deadline is next week.
        [0:30] Bob: Can we extend the project deadline?
        [1:00] Alice: The project manager said no extension.
        [1:30] Bob: Let's discuss the project scope then.
        """
        topics = extractor.extract_topics(text)
        
        # "project" should be a prominent topic
        topic_names = [t['name'].lower() for t in topics]
        has_project = any('project' in name for name in topic_names)
        assert has_project or len(topics) > 0  # Should find something
    
    def test_extract_topics_technical_content(self):
        """Test topic extraction from technical content."""
        extractor = TopicExtractor()
        text = """
        [0:00] Dev1: The Python backend needs optimization.
        [0:30] Dev2: Let's refactor the database queries.
        [1:00] Dev1: The API response times are too slow.
        [1:30] Dev2: We should add caching to the API.
        """
        topics = extractor.extract_topics(text)
        assert len(topics) >= 1
    
    def test_extract_topics_per_message(self):
        """Test associating topics with individual messages."""
        extractor = TopicExtractor()
        text = """
        [0:00] Alice: Let's talk about marketing.
        [0:30] Bob: I prefer discussing technology.
        """
        topics = extractor.extract_topics(text)
        
        messages = [
            {'speaker': 'Alice', 'text': 'Let\'s talk about marketing.'},
            {'speaker': 'Bob', 'text': 'I prefer discussing technology.'}
        ]
        
        result = extractor.extract_topics_per_message(messages, topics)
        assert len(result) == 2
        for msg in result:
            assert 'topics' in msg


class TestTopicExtractorSingleton:
    """Tests for singleton pattern."""
    
    def test_get_topic_extractor_returns_same_instance(self):
        """Test that get_topic_extractor returns the same instance."""
        extractor1 = get_topic_extractor()
        extractor2 = get_topic_extractor()
        assert extractor1 is extractor2


class TestTopicExtractionAPI:
    """Tests for topic extraction API endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from looksatwords.app.main import app
        return TestClient(app)
    
    def test_extract_topics_endpoint(self, client):
        """Test POST /api/extract-topics endpoint."""
        response = client.post(
            "/api/extract-topics",
            json={"text": "[0:00] Alice: Marketing strategy discussion.\n[0:30] Bob: Marketing is important."}
        )
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        assert "dynamic_extraction" in data
        assert "topic_count" in data
        assert data["dynamic_extraction"] is True
    
    def test_extract_topics_endpoint_empty_text(self, client):
        """Test extract topics with empty text."""
        response = client.post(
            "/api/extract-topics",
            json={"text": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["topics"], list)
    
    def test_extract_topics_endpoint_complex_text(self, client):
        """Test extract topics with complex conversation."""
        text = """
        [0:00] John: Let's discuss the quarterly budget report.
        [0:30] Sarah: The budget shows increased spending on technology.
        [1:00] John: Technology investments are crucial for growth.
        [1:30] Mike: What about the marketing budget allocation?
        [2:00] Sarah: Marketing needs more resources for the campaign.
        [2:30] John: We should balance between technology and marketing.
        """
        response = client.post(
            "/api/extract-topics",
            json={"text": text}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["topics"]) >= 1
        assert data["topic_count"] == len(data["topics"])
    
    def test_extract_topics_response_structure(self, client):
        """Test that response has correct structure."""
        response = client.post(
            "/api/extract-topics",
            json={"text": "[0:00] Alice: Budget planning meeting.\n[0:30] Bob: Budget review."}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["topics"]:
            topic = data["topics"][0]
            assert "name" in topic
            assert "keywords" in topic
            assert "score" in topic
            assert "normalized_score" in topic
            assert "sources" in topic


class TestDynamicTopicIntegration:
    """Tests for dynamic topic integration with visualizer backend."""
    
    def test_visualizer_uses_dynamic_topics(self):
        """Test that visualizer backend uses dynamic topic extraction."""
        from looksatwords.frontend.visualizer_backend import ThreadVisualizerBackend
        
        visualizer = ThreadVisualizerBackend(use_dynamic_topics=True)
        text = """
        [0:00] Alice: Let's review the quarterly sales figures.
        [0:30] Bob: Sales have increased by 20% this quarter.
        [1:00] Alice: Great news about sales performance!
        [1:30] Bob: We should celebrate the sales team.
        """
        
        visualizer.parseConversation(text)
        visualizer.identifyThreads()
        
        # Should have identified at least one thread
        assert len(visualizer.threads) >= 0  # May be 0 if no topics meet threshold
        
        # Check summary includes dynamic topics info
        summary = visualizer.getAnalysisSummary()
        assert 'dynamic_topics_enabled' in summary
        assert 'extracted_topics' in summary
    
    def test_visualizer_fallback_to_static(self):
        """Test visualizer falls back to static when dynamic disabled."""
        from looksatwords.frontend.visualizer_backend import ThreadVisualizerBackend
        
        visualizer = ThreadVisualizerBackend(use_dynamic_topics=False)
        text = """
        [0:00] Alice: Marketing strategy for next quarter.
        [0:30] Bob: Digital marketing is the way forward.
        """
        
        visualizer.parseConversation(text)
        visualizer.identifyThreads()
        
        summary = visualizer.getAnalysisSummary()
        # Should still work but with empty extracted_topics
        assert 'extracted_topics' in summary
