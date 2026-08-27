"""
E2E tests for the conversation thread flow visualizer frontend.
Tests HTML structure, JavaScript functionality, and interactive elements.
"""
import pytest
from pathlib import Path
import re


class TestFrontendStructure:
    """Test the HTML structure and content of the frontend."""

    @pytest.fixture
    def frontend_html(self):
        """Load the frontend HTML file."""
        frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
        assert frontend_path.exists(), "Frontend HTML file not found"
        with open(frontend_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def visualizer_js(self):
        """Load the visualizer JavaScript file."""
        js_path = Path(__file__).parent.parent / "frontend" / "visualizer.js"
        assert js_path.exists(), "Visualizer JavaScript file not found"
        with open(js_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_frontend_html_exists(self, frontend_html):
        """Test that frontend HTML file exists and contains content."""
        assert len(frontend_html) > 0
        assert "<!DOCTYPE html>" in frontend_html or "<html" in frontend_html

    def test_frontend_has_required_elements(self, frontend_html):
        """Test that frontend has required UI elements."""
        required_elements = [
            'id="textInput"',
            'id="visualization"',
            'id="threadAnalysis"',
            'id="progressFill"',
            'id="timeDisplay"',
            'id="pathContainer"'
            # Note: analyticsPanel is created dynamically by JavaScript
        ]
        for element in required_elements:
            assert element in frontend_html, f"Missing required element: {element}"

    def test_frontend_shell_has_its_own_buttons(self, frontend_html):
        """The controls the static shell owns, which is not every control.

        Export and Import are deliberately absent here: analytics-panel.js
        writes them into the DOM when the panel renders, so asserting them
        against the shell file measures where the markup lives rather than
        whether the button reaches the user. `test_e2e.py` is the assertion
        that can tell those apart; this one only pins the shell.
        """
        buttons = [
            'Analyze',
            'Play',
            'Pause',
            'Reset',
            'Sample',
            'Generate',
            'Load',
        ]
        for button in buttons:
            assert button in frontend_html, f"Missing button: {button}"

    def test_export_and_import_are_rendered_by_the_panel(self):
        """Where the two controls the shell does not carry actually come from."""
        panel = (Path(__file__).parent.parent
                 / "frontend" / "js" / "analytics-panel.js").read_text(encoding='utf-8')
        assert 'Export Database' in panel
        assert 'Import Database' in panel

    def test_frontend_has_styling(self, frontend_html):
        """Test that frontend includes CSS styling."""
        # Check for inline style OR external stylesheet link
        assert "<style>" in frontend_html or "visualizer.css" in frontend_html
        # Check that CSS classes are used in HTML
        # These are all CSS classes that are defined and used in the frontend
        assert "thread-node" in frontend_html or "analysis-grid" in frontend_html
        assert "playback-controls" in frontend_html or "control-buttons" in frontend_html

    def test_frontend_links_visualizer_js(self, frontend_html):
        """Test that frontend links to JavaScript (modular app.js or legacy visualizer.js)."""
        # Check for either modular architecture (app.js) or legacy (visualizer.js)
        has_modular = "app.js" in frontend_html
        has_legacy = "visualizer.js" in frontend_html
        assert has_modular or has_legacy, "No JavaScript entry point found"
        # Check for script tag
        assert "<script" in frontend_html

    def test_frontend_includes_anime_library(self, frontend_html):
        """Test that frontend includes Anime.js library for animations."""
        assert "anime" in frontend_html or "anime.js" in frontend_html

    def test_visualizer_js_exists(self, visualizer_js):
        """Test that visualizer.js exists and contains code."""
        assert len(visualizer_js) > 0

    def test_visualizer_js_has_class_definition(self, visualizer_js):
        """Test that visualizer.js defines ThreadVisualizer class."""
        assert "class ThreadVisualizer" in visualizer_js
        assert "constructor()" in visualizer_js

    def test_visualizer_js_has_key_methods(self, visualizer_js):
        """Test that visualizer.js has required methods."""
        required_methods = [
            'parseConversation',
            'identifyThreads',
            'detectTangents',
            'createVisualization',
            'animateThreadsAppearance',
            'playThreadEvolution'
        ]
        for method in required_methods:
            assert f"{method}(" in visualizer_js, f"Missing method: {method}"

    def test_visualizer_js_instantiation(self, visualizer_js):
        """Test that visualizer.js creates visualizer instance."""
        assert "const visualizer = new ThreadVisualizer()" in visualizer_js

    def test_visualizer_js_has_event_handlers(self, visualizer_js):
        """Test that visualizer.js defines event handler functions."""
        handlers = [
            'analyzeThreads',
            'playThreadEvolution',
            'pausePlayback',
            'resetVisualization',
            'seekToPosition',
            'loadSampleConversation'
        ]
        for handler in handlers:
            assert f"function {handler}(" in visualizer_js, f"Missing handler: {handler}"

    def test_frontend_accessibility(self, frontend_html):
        """Test basic accessibility features."""
        # Check for lang attribute
        assert 'lang=' in frontend_html
        # Check for title tag
        assert '<title>' in frontend_html
        # Check for meta viewport
        assert 'viewport' in frontend_html

    def test_visualizer_has_topic_keywords(self, visualizer_js):
        """Test that visualizer defines topic keywords."""
        assert "topicKeywords" in visualizer_js
        # Check for expected topics
        topics = ['marketing', 'technology', 'environment', 'business', 'finance']
        for topic in topics:
            assert f"'{topic}'" in visualizer_js or f'"{topic}"' in visualizer_js

    def test_visualizer_has_tangent_triggers(self, visualizer_js):
        """Test that visualizer defines tangent trigger words."""
        assert "tangentTriggers" in visualizer_js
        # Check for expected triggers
        triggers = ['but', 'however', 'tangent', 'side note']
        for trigger in triggers:
            assert trigger in visualizer_js

    def test_visualizer_has_color_arrays(self, visualizer_js):
        """Test that visualizer defines color arrays for threads and speakers."""
        assert "threadColors" in visualizer_js
        assert "speakerColors" in visualizer_js
        # Check for hex color patterns
        assert re.search(r'#[0-9a-fA-F]{6}', visualizer_js), "Missing color definitions"

    def test_frontend_has_explanation_text(self, frontend_html):
        """Test that frontend has helpful explanation text."""
        assert "Thread" in frontend_html
        assert "Conversation" in frontend_html or "conversation" in frontend_html

    def test_visualizer_svg_support(self, visualizer_js):
        """Test that visualizer uses SVG for drawing."""
        assert "createElementNS" in visualizer_js
        assert "http://www.w3.org/2000/svg" in visualizer_js

    def test_visualizer_path_generation(self, visualizer_js):
        """Test that visualizer has path generation logic."""
        assert "generatePathData" in visualizer_js
        assert "bezier" in visualizer_js.lower() or "cubic" in visualizer_js.lower() or "C " in visualizer_js

    def test_visualizer_animation_logic(self, visualizer_js):
        """Test that visualizer integrates with Anime.js."""
        assert "anime({" in visualizer_js or "anime.{" in visualizer_js
        assert "duration:" in visualizer_js
        assert "easing:" in visualizer_js

    def test_visualizer_formatting(self, visualizer_js):
        """Test that visualizer has time formatting logic."""
        assert "formatTime" in visualizer_js
        # Check for time formatting pattern
        assert ".padStart" in visualizer_js or "toString().padStart" in visualizer_js


class TestFrontendDirectoryStructure:
    """Test the frontend directory structure."""

    def test_frontend_directory_exists(self):
        """Test that frontend directory exists."""
        frontend_dir = Path(__file__).parent.parent / "frontend"
        assert frontend_dir.exists()
        assert frontend_dir.is_dir()

    def test_frontend_html_file_exists(self):
        """Test that index.html exists."""
        html_file = Path(__file__).parent.parent / "frontend" / "index.html"
        assert html_file.exists()
        assert html_file.is_file()

    def test_frontend_js_file_exists(self):
        """Test that visualizer.js exists."""
        js_file = Path(__file__).parent.parent / "frontend" / "visualizer.js"
        assert js_file.exists()
        assert js_file.is_file()

    def test_frontend_files_are_readable(self):
        """Test that frontend files can be read."""
        html_file = Path(__file__).parent.parent / "frontend" / "index.html"
        js_file = Path(__file__).parent.parent / "frontend" / "visualizer.js"
        
        with open(html_file, 'r', encoding='utf-8') as f:
            assert len(f.read()) > 0
        
        with open(js_file, 'r', encoding='utf-8') as f:
            assert len(f.read()) > 0

    def test_frontend_js_file_size(self):
        """Test that visualizer.js has substantial content."""
        js_file = Path(__file__).parent.parent / "frontend" / "visualizer.js"
        size = js_file.stat().st_size
        # Should be at least 10KB for full implementation
        assert size > 10000, f"visualizer.js too small: {size} bytes"

    def test_frontend_html_file_size(self):
        """Test that index.html has substantial content."""
        html_file = Path(__file__).parent.parent / "frontend" / "index.html"
        size = html_file.stat().st_size
        # Modular version is smaller (CSS extracted), minimum 3KB
        assert size > 3000, f"index.html too small: {size} bytes"


class TestModularJSArchitecture:
    """Test the modular ES6 JavaScript architecture."""

    @pytest.fixture
    def js_dir(self):
        """Get the JS modules directory."""
        return Path(__file__).parent.parent / "frontend" / "js"

    @pytest.fixture
    def css_dir(self):
        """Get the CSS directory."""
        return Path(__file__).parent.parent / "frontend" / "css"

    def test_js_directory_exists(self, js_dir):
        """Test that js/ directory exists."""
        assert js_dir.exists()
        assert js_dir.is_dir()

    def test_css_directory_exists(self, css_dir):
        """Test that css/ directory exists."""
        assert css_dir.exists()
        assert css_dir.is_dir()

    def test_all_modules_exist(self, js_dir):
        """Test that all required JS modules exist."""
        required_modules = [
            'config.js',
            'models.js',
            'parser.js',
            'thread-analyzer.js',
            'tangent-detector.js',
            'renderer.js',
            'animation.js',
            'reporter.js',
            'api-client.js',
            'app.js'
        ]
        for module in required_modules:
            module_path = js_dir / module
            assert module_path.exists(), f"Missing module: {module}"

    def test_css_file_exists(self, css_dir):
        """Test that visualizer.css exists."""
        css_file = css_dir / "visualizer.css"
        assert css_file.exists(), "Missing visualizer.css"

    def test_css_file_has_content(self, css_dir):
        """Test that visualizer.css has substantial content."""
        css_file = css_dir / "visualizer.css"
        size = css_file.stat().st_size
        assert size > 5000, f"visualizer.css too small: {size} bytes"


class TestConfigModule:
    """Test the config.js module."""

    @pytest.fixture
    def config_js(self):
        """Load config.js content."""
        config_path = Path(__file__).parent.parent / "frontend" / "js" / "config.js"
        with open(config_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_config(self, config_js):
        """Test that config exports CONFIG object."""
        assert "export const CONFIG" in config_js or "export { CONFIG" in config_js

    def test_has_api_config(self, config_js):
        """Test that config has API settings."""
        assert "api:" in config_js or "api :" in config_js
        assert "endpoint" in config_js

    def test_has_color_palettes(self, config_js):
        """Test that config has color palettes."""
        assert "colors:" in config_js or "colors :" in config_js
        assert "threads" in config_js
        assert "speakers" in config_js
        assert "tangents" in config_js

    def test_has_dimensions(self, config_js):
        """Test that config has dimension settings."""
        assert "dimensions:" in config_js or "dimensions :" in config_js
        assert "canvasPadding" in config_js
        assert "threadSpacing" in config_js

    def test_has_animation_settings(self, config_js):
        """Test that config has animation settings."""
        assert "animation:" in config_js or "animation :" in config_js
        assert "duration" in config_js.lower()

    def test_has_keywords(self, config_js):
        """Test that config has topic keywords."""
        assert "keywords:" in config_js or "keywords :" in config_js
        assert "topics" in config_js
        assert "tangentTriggers" in config_js
        assert "resolutionTriggers" in config_js

    def test_has_sample_conversation(self, config_js):
        """Test that config has sample conversation."""
        assert "sampleConversation" in config_js


class TestModelsModule:
    """Test the models.js module."""

    @pytest.fixture
    def models_js(self):
        """Load models.js content."""
        models_path = Path(__file__).parent.parent / "frontend" / "js" / "models.js"
        with open(models_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_speaker_class(self, models_js):
        """Test that models exports Speaker class."""
        assert "export class Speaker" in models_js

    def test_exports_timepoint_class(self, models_js):
        """Test that models exports TimePoint class."""
        assert "export class TimePoint" in models_js

    def test_exports_thread_class(self, models_js):
        """Test that models exports Thread class."""
        assert "export class Thread" in models_js

    def test_exports_tangent_class(self, models_js):
        """Test that models exports Tangent class."""
        assert "export class Tangent" in models_js

    def test_exports_conversation_data_class(self, models_js):
        """Test that models exports ConversationData class."""
        assert "export class ConversationData" in models_js

    def test_exports_format_time_function(self, models_js):
        """Test that models exports formatTime function."""
        assert "export function formatTime" in models_js

    def test_speaker_has_get_initial(self, models_js):
        """Test that Speaker has getInitial method."""
        assert "getInitial(" in models_js

    def test_thread_has_add_point(self, models_js):
        """Test that Thread has addPoint method."""
        assert "addPoint(" in models_js

    def test_tangent_has_get_color(self, models_js):
        """Test that Tangent has getColor method."""
        assert "getColor(" in models_js


class TestParserModule:
    """Test the parser.js module."""

    @pytest.fixture
    def parser_js(self):
        """Load parser.js content."""
        parser_path = Path(__file__).parent.parent / "frontend" / "js" / "parser.js"
        with open(parser_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_conversation_parser(self, parser_js):
        """Test that parser exports ConversationParser class."""
        assert "export class ConversationParser" in parser_js

    def test_has_parse_method(self, parser_js):
        """Test that parser has parse method."""
        assert "parse(" in parser_js

    def test_has_parse_line_method(self, parser_js):
        """Test that parser has parseLine method."""
        assert "parseLine(" in parser_js

    def test_has_get_speakers_method(self, parser_js):
        """Test that parser has getSpeakers method."""
        assert "getSpeakers(" in parser_js

    def test_has_get_total_duration_method(self, parser_js):
        """Test that parser has getTotalDuration method."""
        assert "getTotalDuration(" in parser_js

    def test_imports_models(self, parser_js):
        """Test that parser imports from models."""
        assert "import" in parser_js
        assert "models.js" in parser_js


class TestThreadAnalyzerModule:
    """Test the thread-analyzer.js module."""

    @pytest.fixture
    def thread_analyzer_js(self):
        """Load thread-analyzer.js content."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "thread-analyzer.js"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_thread_analyzer(self, thread_analyzer_js):
        """Test that module exports ThreadAnalyzer class."""
        assert "export class ThreadAnalyzer" in thread_analyzer_js

    def test_has_analyze_method(self, thread_analyzer_js):
        """Test that ThreadAnalyzer has analyze method."""
        assert "analyze(" in thread_analyzer_js

    def test_has_identify_topics_method(self, thread_analyzer_js):
        """Test that ThreadAnalyzer has identifyTopics method."""
        assert "identifyTopics(" in thread_analyzer_js

    def test_imports_config(self, thread_analyzer_js):
        """Test that module imports config."""
        assert "config.js" in thread_analyzer_js

    def test_imports_models(self, thread_analyzer_js):
        """Test that module imports models."""
        assert "models.js" in thread_analyzer_js


class TestTangentDetectorModule:
    """Test the tangent-detector.js module."""

    @pytest.fixture
    def tangent_detector_js(self):
        """Load tangent-detector.js content."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "tangent-detector.js"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_tangent_detector(self, tangent_detector_js):
        """Test that module exports TangentDetector class."""
        assert "export class TangentDetector" in tangent_detector_js

    def test_has_detect_method(self, tangent_detector_js):
        """Test that TangentDetector has detect method."""
        assert "detect(" in tangent_detector_js

    def test_has_analyze_tangent_method(self, tangent_detector_js):
        """Test that TangentDetector has analyzeTangent method."""
        assert "analyzeTangent(" in tangent_detector_js

    def test_has_is_tangent_trigger_method(self, tangent_detector_js):
        """Test that TangentDetector has isTangentTrigger method."""
        assert "isTangentTrigger(" in tangent_detector_js

    def test_has_returns_to_main_thread_method(self, tangent_detector_js):
        """Test that TangentDetector has returnsToMainThread method."""
        assert "returnsToMainThread(" in tangent_detector_js


class TestRendererModule:
    """Test the renderer.js module."""

    @pytest.fixture
    def renderer_js(self):
        """Load renderer.js content."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "renderer.js"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_visualization_renderer(self, renderer_js):
        """Test that module exports VisualizationRenderer class."""
        assert "export class VisualizationRenderer" in renderer_js

    def test_has_render_method(self, renderer_js):
        """Test that VisualizationRenderer has render method."""
        assert "render(" in renderer_js

    def test_has_clear_method(self, renderer_js):
        """Test that VisualizationRenderer has clear method."""
        assert "clear(" in renderer_js

    def test_has_render_threads_method(self, renderer_js):
        """Test that VisualizationRenderer has renderThreads method."""
        assert "renderThreads(" in renderer_js

    def test_has_render_tangents_method(self, renderer_js):
        """Test that VisualizationRenderer has renderTangents method."""
        assert "renderTangents(" in renderer_js

    def test_has_render_timeline_method(self, renderer_js):
        """Test that VisualizationRenderer has renderTimeline method."""
        assert "renderTimeline(" in renderer_js

    def test_has_calculate_x_method(self, renderer_js):
        """Test that VisualizationRenderer has calculateX method."""
        assert "calculateX(" in renderer_js

    def test_has_calculate_y_method(self, renderer_js):
        """Test that VisualizationRenderer has calculateY method."""
        assert "calculateY(" in renderer_js

    def test_uses_svg(self, renderer_js):
        """Test that renderer uses SVG elements."""
        assert "createElementNS" in renderer_js
        assert "svg" in renderer_js.lower()


class TestAnimationModule:
    """Test the animation.js module."""

    @pytest.fixture
    def animation_js(self):
        """Load animation.js content."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "animation.js"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_animation_controller(self, animation_js):
        """Test that module exports AnimationController class."""
        assert "export class AnimationController" in animation_js

    def test_has_animate_appearance_method(self, animation_js):
        """Test that AnimationController has animateAppearance method."""
        assert "animateAppearance(" in animation_js

    def test_has_start_playback_method(self, animation_js):
        """Test that AnimationController has startPlayback method."""
        assert "startPlayback(" in animation_js

    def test_has_stop_playback_method(self, animation_js):
        """Test that AnimationController has stopPlayback method."""
        assert "stopPlayback(" in animation_js

    def test_has_pause_playback_method(self, animation_js):
        """Test that AnimationController has pausePlayback method."""
        assert "pausePlayback(" in animation_js

    def test_has_seek_to_time_method(self, animation_js):
        """Test that AnimationController has seekToTime method."""
        assert "seekToTime(" in animation_js

    def test_uses_anime_js(self, animation_js):
        """Test that animation controller uses anime.js."""
        assert "anime(" in animation_js or "anime({" in animation_js


class TestReporterModule:
    """Test the reporter.js module."""

    @pytest.fixture
    def reporter_js(self):
        """Load reporter.js content."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "reporter.js"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_analysis_reporter(self, reporter_js):
        """Test that module exports AnalysisReporter class."""
        assert "export class AnalysisReporter" in reporter_js

    def test_has_generate_report_method(self, reporter_js):
        """Test that AnalysisReporter has generateReport method."""
        assert "generateReport(" in reporter_js

    def test_has_clear_method(self, reporter_js):
        """Test that AnalysisReporter has clear method."""
        assert "clear(" in reporter_js

    def test_has_add_thread_analysis_method(self, reporter_js):
        """Test that AnalysisReporter has addThreadAnalysis method."""
        assert "addThreadAnalysis(" in reporter_js

    def test_has_add_tangent_analysis_method(self, reporter_js):
        """Test that AnalysisReporter has addTangentAnalysis method."""
        assert "addTangentAnalysis(" in reporter_js


class TestApiClientModule:
    """Test the api-client.js module."""

    @pytest.fixture
    def api_client_js(self):
        """Load api-client.js content."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "api-client.js"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_api_client(self, api_client_js):
        """Test that module exports ApiClient class."""
        assert "export class ApiClient" in api_client_js

    def test_exports_ui_feedback(self, api_client_js):
        """Test that module exports UIFeedback class."""
        assert "export class UIFeedback" in api_client_js

    def test_has_check_health_method(self, api_client_js):
        """Test that ApiClient has checkHealth method."""
        assert "checkHealth(" in api_client_js

    def test_has_analyze_conversation_method(self, api_client_js):
        """Test that ApiClient has analyzeConversation method."""
        assert "analyzeConversation(" in api_client_js

    def test_has_list_conversations_method(self, api_client_js):
        """Test that ApiClient has listConversations method."""
        assert "listConversations(" in api_client_js

    def test_has_delete_conversation_method(self, api_client_js):
        """Test that ApiClient has deleteConversation method."""
        assert "deleteConversation(" in api_client_js

    def test_uses_fetch(self, api_client_js):
        """Test that ApiClient uses fetch API."""
        assert "fetch(" in api_client_js

    def test_ui_feedback_has_show_loading(self, api_client_js):
        """Test that UIFeedback has showLoading method."""
        assert "showLoading(" in api_client_js

    def test_ui_feedback_has_show_message(self, api_client_js):
        """Test that UIFeedback has showMessage method."""
        assert "showMessage(" in api_client_js


class TestAppModule:
    """Test the app.js module."""

    @pytest.fixture
    def app_js(self):
        """Load app.js content."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "app.js"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_main_app(self, app_js):
        """Test that module exports ConversationVisualizerApp class."""
        assert "export class ConversationVisualizerApp" in app_js

    def test_has_init_method(self, app_js):
        """Test that app has init method."""
        assert "init(" in app_js

    def test_has_analyze_method(self, app_js):
        """Test that app has analyze method."""
        assert "analyze(" in app_js

    def test_has_play_method(self, app_js):
        """Test that app has play method."""
        assert "play(" in app_js

    def test_has_pause_method(self, app_js):
        """Test that app has pause method."""
        assert "pause(" in app_js

    def test_has_reset_method(self, app_js):
        """Test that app has reset method."""
        assert "reset(" in app_js

    def test_has_load_sample_method(self, app_js):
        """Test that app has loadSample method."""
        assert "loadSample(" in app_js

    def test_imports_all_modules(self, app_js):
        """Test that app imports all required modules."""
        required_imports = [
            'config.js',
            'models.js',
            'parser.js',
            'thread-analyzer.js',
            'tangent-detector.js',
            'renderer.js',
            'animation.js',
            'reporter.js',
            'api-client.js'
        ]
        for module in required_imports:
            assert module in app_js, f"Missing import: {module}"

    def test_exports_global_functions(self, app_js):
        """Test that app exports global functions for HTML handlers."""
        assert "window.analyzeThreads" in app_js
        assert "window.playThreadEvolution" in app_js
        assert "window.resetVisualization" in app_js
        assert "window.loadSampleConversation" in app_js

    def test_initializes_on_dom_ready(self, app_js):
        """Test that app initializes on DOMContentLoaded."""
        assert "DOMContentLoaded" in app_js


class TestVisualizerCSS:
    """Test the visualizer.css file."""

    @pytest.fixture
    def visualizer_css(self):
        """Load visualizer.css content."""
        css_path = Path(__file__).parent.parent / "frontend" / "css" / "visualizer.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_has_css_custom_properties(self, visualizer_css):
        """Test that CSS uses custom properties."""
        assert ":root" in visualizer_css
        assert "--" in visualizer_css

    def test_has_container_styles(self, visualizer_css):
        """Test that CSS has container styles."""
        assert ".container" in visualizer_css

    def test_has_button_styles(self, visualizer_css):
        """Test that CSS has button styles."""
        assert ".btn" in visualizer_css

    def test_has_visualization_styles(self, visualizer_css):
        """Test that CSS has visualization container styles."""
        assert ".visualization-container" in visualizer_css

    def test_has_thread_node_styles(self, visualizer_css):
        """Test that CSS has thread node styles."""
        assert ".thread-node" in visualizer_css

    def test_has_timeline_styles(self, visualizer_css):
        """Test that CSS has timeline styles."""
        assert ".timeline" in visualizer_css

    def test_has_responsive_styles(self, visualizer_css):
        """Test that CSS has responsive media queries."""
        assert "@media" in visualizer_css

    def test_has_animation_keyframes(self, visualizer_css):
        """Test that CSS has animation keyframes."""
        assert "@keyframes" in visualizer_css or "animation" in visualizer_css

    def test_has_analytics_panel_styles(self, visualizer_css):
        """Test that CSS has analytics panel styles."""
        assert "#analyticsPanel" in visualizer_css or ".analytics-panel" in visualizer_css

    def test_has_speaker_card_styles(self, visualizer_css):
        """Test that CSS has speaker analytics card styles."""
        assert ".speaker-card" in visualizer_css

    def test_has_word_frequency_styles(self, visualizer_css):
        """Test that CSS has word frequency styles."""
        assert ".word-freq" in visualizer_css or ".word-bar" in visualizer_css

    def test_has_pos_distribution_styles(self, visualizer_css):
        """Test that CSS has POS distribution styles."""
        assert ".pos-grid" in visualizer_css or ".pos-item" in visualizer_css


class TestAnalyticsPanelModule:
    """Test the analytics-panel.js module."""

    @pytest.fixture
    def analytics_panel_js(self):
        """Load analytics-panel.js content."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "analytics-panel.js"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_exports_analytics_panel(self, analytics_panel_js):
        """Test that module exports AnalyticsPanel class."""
        assert "export class AnalyticsPanel" in analytics_panel_js

    def test_has_render_method(self, analytics_panel_js):
        """The panel renders per tab; there is no single `render()` any more."""
        assert "renderCurrentTab(" in analytics_panel_js
        assert "renderAnalyticsTab(" in analytics_panel_js

    def test_has_clear_method(self, analytics_panel_js):
        """Test that AnalyticsPanel has clear method."""
        assert "clear(" in analytics_panel_js

    def test_has_toggle_method(self, analytics_panel_js):
        """Test that AnalyticsPanel has toggle method."""
        assert "toggle(" in analytics_panel_js

    def test_has_overview_card_renderer(self, analytics_panel_js):
        """Test that AnalyticsPanel has renderOverviewCard method."""
        assert "renderOverviewCard(" in analytics_panel_js

    def test_has_sentiment_chart_renderer(self, analytics_panel_js):
        """Test that AnalyticsPanel has a sentiment chart renderer."""
        assert "renderMiniSentimentChart(" in analytics_panel_js

    def test_has_word_frequency_renderer(self, analytics_panel_js):
        """Test that AnalyticsPanel has renderWordFrequency method."""
        assert "renderWordFrequency(" in analytics_panel_js

    def test_has_pos_distribution_renderer(self, analytics_panel_js):
        """Test that AnalyticsPanel has renderPOSDistribution method."""
        assert "renderPOSDistribution(" in analytics_panel_js

    def test_has_speaker_analytics_renderer(self, analytics_panel_js):
        """Test that AnalyticsPanel has renderSpeakerAnalytics method."""
        assert "renderSpeakerAnalytics(" in analytics_panel_js

    def test_has_sentiment_helpers(self, analytics_panel_js):
        """The one sentiment helper the panel still factors out.

        `getSentimentColor()` is gone: renderMiniSentimentChart picks the bar
        colour inline from the compound score. Asserting a helper that nothing
        calls would pin a shape the code has left.
        """
        assert "getSentimentEmoji(" in analytics_panel_js

    def test_imports_config(self, analytics_panel_js):
        """Test that module imports config."""
        assert "config.js" in analytics_panel_js

    def test_chart_is_drawn_as_css_bars(self, analytics_panel_js):
        """The sentiment chart draws div bars, not SVG.

        This asserted SVG and passed for years on the word "svg" appearing
        anywhere in the file. The chart never drew one after the tabs
        refactor; it sizes a row of divs by compound score.
        """
        assert "renderMiniSentimentChart(" in analytics_panel_js
        assert "<svg" not in analytics_panel_js
