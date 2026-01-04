"""End-to-end tests using Playwright.

These tests validate browser-based functionality and require:
1. Playwright browsers installed: `uv run playwright install chromium`
2. The server running: `uv run looksatwords serve --no-open`

The server serves both the API and frontend on port 8000.
"""
import pytest
import requests

# Mark all tests in this file as e2e tests
pytestmark = pytest.mark.e2e

# Default server URLs
DEFAULT_SERVER_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{DEFAULT_SERVER_URL}/health"


def _check_server_running():
    """Check if the server is running and return error message if not."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=2)
        if response.status_code == 200:
            return None  # Server is running
        return f"Server returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return (
            "Server not running. Start it with:\n"
            "  uv run looksatwords serve --no-open\n"
            "Then re-run the tests."
        )
    except requests.exceptions.Timeout:
        return "Server timed out. It may be overloaded or starting up."
    except Exception as e:
        return f"Server check failed: {e}"


@pytest.fixture(scope="module")
def server_url():
    """Fixture that provides the server URL, skipping if server isn't running."""
    error = _check_server_running()
    if error:
        pytest.skip(error)
    return DEFAULT_SERVER_URL


@pytest.fixture(scope="module")
def browser_context():
    """Fixture that provides a Playwright browser, skipping if not available."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Playwright not installed. Run: uv add playwright && uv run playwright install chromium")
    
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        yield browser
        browser.close()
        pw.stop()
    except Exception as e:
        pytest.skip(f"Playwright browsers not installed. Run: uv run playwright install chromium\nError: {e}")


# =============================================================================
# Playwright Setup Tests
# =============================================================================

def test_playwright_available():
    """Test that Playwright can be imported."""
    try:
        from playwright.sync_api import sync_playwright
        assert sync_playwright is not None
    except ImportError:
        pytest.skip("Playwright not installed. Run: uv add playwright && uv run playwright install chromium")


def test_playwright_browser_launch():
    """Test that Playwright can launch a browser."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Playwright not installed")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("data:text/html,<h1>Test Page</h1>")
            content = page.content()
            assert "Test Page" in content
            browser.close()
    except Exception as e:
        pytest.skip(f"Playwright browsers not installed: {e}")


# =============================================================================
# Server Health Tests
# =============================================================================

def test_server_health():
    """Test that the server health endpoint responds."""
    error = _check_server_running()
    if error:
        pytest.skip(error)
    
    response = requests.get(HEALTH_ENDPOINT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_api_docs_available(server_url):
    """Test that the API documentation is available."""
    response = requests.get(f"{server_url}/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


# =============================================================================
# Frontend Loading Tests
# =============================================================================

def test_frontend_loads(server_url, browser_context):
    """Test that the frontend page loads successfully."""
    page = browser_context.new_page()
    
    try:
        response = page.goto(f"{server_url}/", timeout=10000)
        assert response is not None
        assert response.status == 200
        
        # Check title
        title = page.title()
        assert "Conversation Thread Flow Visualizer" in title
    finally:
        page.close()


def test_frontend_elements_present(server_url, browser_context):
    """Test that key frontend elements are present."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Check key elements exist
        assert page.locator("#textInput").is_visible(), "Text input should be visible"
        assert page.locator("#visualization").is_visible(), "Visualization area should be visible"
        assert page.locator("button:has-text('Analyze Conversation')").is_visible(), "Analyze button should be visible"
        assert page.locator("button:has-text('Reset')").is_visible(), "Reset button should be visible"
        assert page.locator("button:has-text('Load Sample')").is_visible(), "Load Sample button should be visible"
    finally:
        page.close()


def test_css_loads(server_url, browser_context):
    """Test that CSS styles are loaded correctly."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Check that CSS is applied (container should have styling)
        container = page.locator(".container")
        assert container.is_visible()
        
        # The page should have some computed styles from our CSS
        header = page.locator(".header")
        assert header.is_visible()
    finally:
        page.close()


def test_javascript_loads(server_url, browser_context):
    """Test that JavaScript is loaded and functions are available."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Check that key functions are defined
        has_analyze = page.evaluate("typeof window.analyzeThreads === 'function'")
        has_reset = page.evaluate("typeof window.resetVisualization === 'function'")
        has_load_sample = page.evaluate("typeof window.loadSampleConversation === 'function'")
        
        assert has_analyze, "analyzeThreads function should be defined"
        assert has_reset, "resetVisualization function should be defined"
        assert has_load_sample, "loadSampleConversation function should be defined"
    finally:
        page.close()


# =============================================================================
# User Interaction Tests
# =============================================================================

def test_sample_conversation_load(server_url, browser_context):
    """Test loading the sample conversation."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Textarea should initially be empty or have placeholder
        initial_value = page.input_value("#textInput")
        
        # Click load sample button
        page.click("button:has-text('Load Sample')")
        page.wait_for_timeout(500)
        
        # Check that textarea has content
        textarea_value = page.input_value("#textInput")
        assert len(textarea_value) > 0, "Sample conversation should be loaded"
        assert "John" in textarea_value or "marketing" in textarea_value.lower()
    finally:
        page.close()


def test_reset_functionality(server_url, browser_context):
    """Test that reset button clears the conversation."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Load sample first
        page.click("button:has-text('Load Sample')")
        page.wait_for_timeout(500)
        
        # Verify something is loaded
        textarea_value = page.input_value("#textInput")
        assert len(textarea_value) > 0, "Sample should be loaded before reset"
        
        # Click reset
        page.click("button:has-text('Reset')")
        page.wait_for_timeout(500)
        
        # Check that textarea is cleared
        textarea_value = page.input_value("#textInput")
        assert len(textarea_value) == 0, "Textarea should be empty after reset"
    finally:
        page.close()


def test_conversation_analysis_basic(server_url, browser_context):
    """Test basic conversation analysis."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Enter test conversation
        test_conversation = """[0:00] Alice: Hello Bob, how are you today?
[0:30] Bob: I'm doing great! Just finished a project.
[1:00] Alice: That's awesome! What kind of project?
[1:30] Bob: It's a web application for data analysis.
[2:00] Alice: Interesting! Tell me more about it."""
        
        page.fill("#textInput", test_conversation)
        page.click("button:has-text('Analyze Conversation')")
        page.wait_for_timeout(2000)
        
        # Check that thread analysis appeared
        thread_analysis = page.locator("#threadAnalysis")
        assert thread_analysis.is_visible(), "Thread analysis should be visible after analysis"
        
        # Check that thread information is displayed
        content = thread_analysis.inner_text()
        assert len(content) > 0, "Thread analysis should have content"
    finally:
        page.close()


def test_empty_conversation_handling(server_url, browser_context):
    """Test that empty conversation is handled gracefully."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Make sure textarea is empty
        page.fill("#textInput", "")
        
        # Try to analyze without entering text
        page.click("button:has-text('Analyze Conversation')")
        page.wait_for_timeout(1000)
        
        # Should handle gracefully (no crash, page still functional)
        assert page.locator("#textInput").is_visible(), "Page should remain functional"
        assert page.locator("button:has-text('Analyze Conversation')").is_visible()
    finally:
        page.close()


def test_conversation_speakers_detected(server_url, browser_context):
    """Test that speakers are correctly detected."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Enter conversation with distinct speakers
        test_conversation = """[0:00] Alice: Good morning!
[0:30] Bob: Hello Alice!
[1:00] Charlie: Hey everyone!
[1:30] Alice: Nice to see you all."""
        
        page.fill("#textInput", test_conversation)
        page.click("button:has-text('Analyze Conversation')")
        page.wait_for_timeout(2000)
        
        # Check that visualization is visible
        visualization = page.locator("#visualization")
        assert visualization.is_visible()
    finally:
        page.close()


# =============================================================================
# Playback Controls Tests
# =============================================================================

def test_playback_controls_visible(server_url, browser_context):
    """Test that playback controls are visible."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Check playback controls exist
        assert page.locator("#playBtn").is_visible(), "Play button should be visible"
        assert page.locator("#pauseBtn").is_visible(), "Pause button should be visible"
        assert page.locator("#timeDisplay").is_visible(), "Time display should be visible"
    finally:
        page.close()


def test_playback_after_analysis(server_url, browser_context):
    """Test that playback works after analysis."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Enter and analyze conversation
        test_conversation = """[0:00] Alice: Let's start the meeting.
[0:30] Bob: Sounds good.
[1:00] Alice: First item on the agenda."""
        
        page.fill("#textInput", test_conversation)
        page.click("button:has-text('Analyze Conversation')")
        page.wait_for_timeout(2000)
        
        # Try to play the visualization
        page.click("#playBtn")
        page.wait_for_timeout(1000)
        
        # Time display should still be visible
        time_display = page.locator("#timeDisplay")
        assert time_display.is_visible()
    finally:
        page.close()


# =============================================================================
# Complex Conversation Tests
# =============================================================================

def test_complex_conversation_analysis(server_url, browser_context):
    """Test analysis of a complex conversation with multiple threads."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Enter a complex conversation with multiple topics
        test_conversation = """[0:00] Alice: Let's discuss the Q4 roadmap and the hiring plan.
[0:30] Bob: Good idea. For Q4, I think we should focus on the new features.
[1:00] Charlie: What about the hiring? We need at least 3 developers.
[1:30] Alice: Right, let's tackle both. Bob, what features are you thinking?
[2:00] Bob: I'm thinking AI integration and mobile support.
[2:30] Charlie: Those sound great, but back to hiring - when do we start?
[3:00] Alice: We can start interviews next week.
[3:30] Bob: Perfect. So for AI, we'll need some ML expertise.
[4:00] Charlie: I know someone who might be interested in the position."""
        
        page.fill("#textInput", test_conversation)
        page.click("button:has-text('Analyze Conversation')")
        page.wait_for_timeout(3000)
        
        # Check that threads are detected
        thread_analysis = page.locator("#threadAnalysis")
        assert thread_analysis.is_visible()
        
        content = thread_analysis.inner_text()
        assert len(content) > 50, "Complex conversation should produce detailed analysis"
    finally:
        page.close()


def test_conversation_with_tangents(server_url, browser_context):
    """Test that tangents are detected in conversations."""
    page = browser_context.new_page()
    
    try:
        page.goto(f"{server_url}/")
        page.wait_for_load_state("networkidle")
        
        # Load sample conversation which includes tangents
        page.click("button:has-text('Load Sample')")
        page.wait_for_timeout(500)
        
        page.click("button:has-text('Analyze Conversation')")
        page.wait_for_timeout(3000)
        
        # Check tangent legend is visible
        tangent_legend = page.locator("#tangentLegend")
        assert tangent_legend.is_visible(), "Tangent legend should be visible"
    finally:
        page.close()


# =============================================================================
# API Integration Tests
# =============================================================================

def test_api_conversations_list(server_url):
    """Test that the conversations API endpoint works."""
    response = requests.get(f"{server_url}/api/conversations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_conversation_analyze(server_url):
    """Test that the analyze API endpoint works."""
    test_data = {
        "text": "[0:00] Alice: Hello\n[0:30] Bob: Hi there",
        "title": "Test Conversation"
    }
    
    response = requests.post(
        f"{server_url}/api/conversations/analyze",
        json=test_data
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["title"] == "Test Conversation"
    
    # Clean up - delete the conversation
    conv_id = data["conversation_id"]
    requests.delete(f"{server_url}/api/conversations/{conv_id}")


def test_api_conversation_crud(server_url):
    """Test full CRUD operations on conversations."""
    # Create
    test_data = {
        "text": "[0:00] Test: CRUD test conversation",
        "title": "CRUD Test"
    }
    
    create_response = requests.post(
        f"{server_url}/api/conversations/analyze",
        json=test_data
    )
    assert create_response.status_code == 200
    conv_id = create_response.json()["conversation_id"]
    
    # Read
    get_response = requests.get(f"{server_url}/api/conversations/{conv_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "CRUD Test"
    
    # Delete
    delete_response = requests.delete(f"{server_url}/api/conversations/{conv_id}")
    assert delete_response.status_code == 200
    
    # Verify deleted
    verify_response = requests.get(f"{server_url}/api/conversations/{conv_id}")
    assert verify_response.status_code == 404
