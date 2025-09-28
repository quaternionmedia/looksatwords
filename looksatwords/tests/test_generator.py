import pytest
from looksatwords.generator import GnewsGenerator


def test_generator():
    """Test the generator, but skip if Ollama is not running."""
    try:
        import ollama
        # Quick check if Ollama is responsive
        ollama.list()
    except Exception:
        pytest.skip("⚠️  Ollama not running - install with: curl -fsSL https://ollama.com/install.sh | sh && ollama pull llama3.1")
    
    try:
        gnews_generator = GnewsGenerator()
        gnews_generator.generate()
        df = gnews_generator.validate()
        assert not df.empty
        
    except Exception as e:
        pytest.fail(f"Generator test failed: {e}")
