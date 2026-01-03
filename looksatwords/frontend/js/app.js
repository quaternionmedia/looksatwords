/**
 * Conversation Visualizer Application
 * Main application controller that orchestrates all modules
 */

import { CONFIG } from './config.js';
import { ConversationData, formatTime } from './models.js';
import { ConversationParser } from './parser.js';
import { ThreadAnalyzer } from './thread-analyzer.js';
import { TangentDetector } from './tangent-detector.js';
import { VisualizationRenderer } from './renderer.js';
import { AnimationController } from './animation.js';
import { AnalysisReporter } from './reporter.js';
import { ApiClient, UIFeedback } from './api-client.js';

/**
 * Main application class
 */
export class ConversationVisualizerApp {
    constructor(options = {}) {
        // Configuration
        this.options = {
            canvasId: options.canvasId || 'visualization',
            inputId: options.inputId || 'textInput',
            analysisId: options.analysisId || 'threadAnalysis',
            useBackend: options.useBackend !== false
        };

        // Initialize modules
        this.parser = new ConversationParser();
        this.renderer = new VisualizationRenderer(this.options.canvasId);
        this.animator = new AnimationController(this.renderer);
        this.reporter = new AnalysisReporter(this.options.analysisId);
        this.apiClient = new ApiClient();

        // Data container
        this.data = new ConversationData();

        // State
        this.initialized = false;
    }

    /**
     * Initialize the application
     */
    async init() {
        if (this.initialized) return;

        console.log('Initializing Conversation Visualizer...');

        // Check backend availability
        if (this.options.useBackend) {
            const backendAvailable = await this.apiClient.checkHealth();
            if (backendAvailable) {
                console.log('✓ Backend API connected');
                UIFeedback.showMessage('✓ Connected to backend', 'success');
            } else {
                console.log('⚠ Backend not available, using local analysis');
                UIFeedback.showMessage('⚠ Backend not available, using local mode', 'warning');
            }
        }

        // Set up keyboard shortcuts
        this.setupKeyboardShortcuts();

        // Set up resize handler
        this.setupResizeHandler();

        this.initialized = true;
        console.log('Conversation Visualizer ready');
    }

    /**
     * Set up keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Check for modifier key
            if (event.ctrlKey || event.metaKey) {
                switch (event.key) {
                    case 'Enter':
                        event.preventDefault();
                        this.analyze();
                        break;
                    case ' ':
                        event.preventDefault();
                        if (this.animator.isPlaying) {
                            this.pause();
                        } else {
                            this.play();
                        }
                        break;
                    case 'r':
                        event.preventDefault();
                        this.reset();
                        break;
                }
            }
        });
    }

    /**
     * Set up window resize handler
     */
    setupResizeHandler() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (this.data.threads.length > 0) {
                    this.renderVisualization();
                }
            }, 100);
        });
    }

    /**
     * Analyze conversation text
     */
    async analyze() {
        const inputEl = document.getElementById(this.options.inputId);
        const text = inputEl?.value?.trim();

        if (!text) {
            alert('Please enter conversation text first.');
            return;
        }

        try {
            UIFeedback.showLoading(true, 'Analyzing conversation...');

            // Clear previous data
            this.data.clear();

            // Try backend analysis first if available
            if (this.options.useBackend && this.apiClient.isAvailable) {
                await this.analyzeWithBackend(text);
            } else {
                // Use local analysis
                this.analyzeLocally(text);
            }

            // Render visualization
            this.renderVisualization();

            // Generate report
            this.reporter.generateReport(
                this.data.threads,
                this.data.tangents,
                this.data.speakers,
                this.data.totalDuration
            );

            // Animate appearance
            setTimeout(() => {
                this.animator.setData(this.data.threads, this.data.tangents, this.data.totalDuration);
                this.animator.animateAppearance();
            }, 100);

            UIFeedback.showLoading(false);

            console.log('Analysis complete:', this.data.getStats());

        } catch (error) {
            UIFeedback.showLoading(false);
            console.error('Analysis failed:', error);
            UIFeedback.showMessage(`Analysis failed: ${error.message}`, 'error');
        }
    }

    /**
     * Analyze using backend API
     * @param {string} text - Conversation text
     */
    async analyzeWithBackend(text) {
        const response = await this.apiClient.analyzeConversation(text);
        
        this.data.conversationId = response.conversation_id;
        this.data.totalDuration = response.total_duration;

        // Populate speakers
        for (const [name, color] of Object.entries(response.speakers)) {
            this.data.speakers.set(name, {
                name: name,
                color: color,
                getInitial: () => name.charAt(0).toUpperCase()
            });
        }

        // Populate threads
        for (const threadData of response.threads) {
            const thread = {
                name: threadData.name,
                color: threadData.color,
                points: threadData.points.map(p => ({
                    time: p.time,
                    intensity: p.intensity,
                    text: p.text,
                    speaker: p.speaker,
                    speakerInfo: { color: p.speaker_color }
                })),
                totalIntensity: threadData.total_intensity
            };
            this.data.threads.push(thread);
        }

        // Populate tangents
        for (const tangentData of response.tangents) {
            const tangent = {
                startTime: tangentData.start_time,
                endTime: tangentData.end_time,
                type: tangentData.tangent_type,
                topics: tangentData.topics,
                startText: tangentData.start_text,
                resolutionText: tangentData.resolution_text,
                sourceThread: this.data.threads[0] || null,
                getColor: () => CONFIG.colors.tangents[tangentData.tangent_type] || CONFIG.colors.tangents.unresolved
            };
            this.data.tangents.push(tangent);
        }

        UIFeedback.showMessage(`✓ Saved (ID: ${response.conversation_id})`, 'success');
    }

    /**
     * Analyze locally without backend
     * @param {string} text - Conversation text
     */
    analyzeLocally(text) {
        // Parse conversation
        this.data.timePoints = this.parser.parse(text);
        this.data.speakers = this.parser.getSpeakers();
        this.data.totalDuration = this.parser.getTotalDuration();

        // Analyze threads
        const threadAnalyzer = new ThreadAnalyzer(this.data.timePoints);
        this.data.threads = threadAnalyzer.analyze();

        // Detect tangents
        const tangentDetector = new TangentDetector(this.data.timePoints, this.data.threads);
        this.data.tangents = tangentDetector.detect();
    }

    /**
     * Render the visualization
     */
    renderVisualization() {
        this.renderer.render(
            this.data.threads,
            this.data.tangents,
            this.data.speakers,
            this.data.totalDuration
        );
    }

    /**
     * Start playback
     */
    play() {
        if (this.data.threads.length === 0) {
            alert('Please analyze a conversation first.');
            return;
        }

        this.animator.startPlayback();
    }

    /**
     * Pause playback
     */
    pause() {
        this.animator.pausePlayback();
    }

    /**
     * Seek to position in timeline
     * @param {MouseEvent} event - Click event
     */
    seekToPosition(event) {
        if (this.data.totalDuration === 0) return;

        const rect = event.target.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const progress = clickX / rect.width;
        const time = progress * this.data.totalDuration;

        this.animator.seekToTime(time);
    }

    /**
     * Reset the visualization
     */
    reset() {
        this.animator.stopPlayback();
        this.data.clear();
        this.renderer.clear();
        this.reporter.clear();

        // Reset progress bar
        const progressFill = document.getElementById('progressFill');
        const timeDisplay = document.getElementById('timeDisplay');
        if (progressFill) progressFill.style.width = '0%';
        if (timeDisplay) timeDisplay.textContent = '0:00 / 0:00';

        // Clear input
        const inputEl = document.getElementById(this.options.inputId);
        if (inputEl) inputEl.value = '';

        console.log('Visualization reset');
    }

    /**
     * Load sample conversation
     */
    loadSample() {
        const inputEl = document.getElementById(this.options.inputId);
        if (inputEl) {
            inputEl.value = CONFIG.sampleConversation;
            console.log('Sample conversation loaded');
        }
    }

    /**
     * Get current conversation statistics
     * @returns {Object} Statistics object
     */
    getStats() {
        return this.data.getStats();
    }
}

// ============ Global Functions for HTML onclick handlers ============

let app = null;

/**
 * Get or create app instance
 */
function getApp() {
    if (!app) {
        app = new ConversationVisualizerApp();
        app.init();
    }
    return app;
}

// Global function exports for HTML onclick handlers
window.analyzeThreads = async function() {
    await getApp().analyze();
};

window.playThreadEvolution = function() {
    getApp().play();
};

window.pausePlayback = function() {
    getApp().pause();
};

window.resetVisualization = function() {
    getApp().reset();
};

window.seekToPosition = function(event) {
    getApp().seekToPosition(event);
};

window.loadSampleConversation = function() {
    getApp().loadSample();
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    getApp();
});

// Export for module usage
export { getApp };
