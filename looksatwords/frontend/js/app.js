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
import { AnalyticsPanel } from './analytics-panel.js';

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
        this.analyticsPanel = new AnalyticsPanel('analyticsPanel');

        // Data container
        this.data = new ConversationData();

        // State
        this.initialized = false;
        this.viewMode = 'topics'; // 'topics' or 'speakers'
        this.animationComplete = false; // Track if initial animation has run
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
            // Backtick to toggle analytics panel (no modifier needed)
            if (event.key === '`' && !event.ctrlKey && !event.metaKey) {
                event.preventDefault();
                this.toggleAnalyticsPanel();
                return;
            }
            
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
     * Toggle the analytics panel popup
     */
    toggleAnalyticsPanel() {
        if (this.analyticsPanel) {
            this.analyticsPanel.togglePopup();
        }
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
                    // If animation already ran, show all nodes immediately
                    if (this.animationComplete) {
                        this.showAllNodesImmediately();
                    }
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
                this.animator.setData(this.data.threads, this.data.tangents, this.data.totalDuration, this.viewMode);
                this.animator.animateAppearance();
                // Mark animation as complete after animations finish
                setTimeout(() => {
                    this.animationComplete = true;
                }, 2500);
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
        // Use the new endpoint that includes analytics
        const response = await this.apiClient.analyzeWithAnalytics(text);
        
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

        // Render analytics panel if analytics data is present
        if (response.analytics || response.sentiment_timeline) {
            this.analyticsPanel.toggle(true);
            this.analyticsPanel.render({
                aggregated: response.analytics,
                sentiment_timeline: response.sentiment_timeline,
                speaker_analytics: response.speaker_analytics,
                nltk_available: true
            });
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
            this.data.totalDuration,
            this.viewMode
        );
    }

    /**
     * Show all nodes and paths immediately (skip animation)
     * Used after initial animation has completed, for resize/toggle operations
     */
    showAllNodesImmediately() {
        // Show all thread nodes
        document.querySelectorAll('.thread-node').forEach(node => {
            node.style.opacity = '1';
            node.style.transform = 'scale(1)';
        });
        // Show all thread paths
        document.querySelectorAll('.thread-path').forEach(path => {
            path.style.opacity = '0.7';
            path.style.strokeDashoffset = '0';
        });
        // Show all tangent arcs
        document.querySelectorAll('.tangent-arc').forEach(path => {
            path.style.opacity = '0.7';
            path.style.strokeDashoffset = '0';
        });
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
     * Toggle view mode between topics and speakers
     */
    toggleViewMode() {
        this.viewMode = this.viewMode === 'topics' ? 'speakers' : 'topics';
        
        // Stop any running animation
        this.animator.stopPlayback();
        
        // Update button text
        const btn = document.getElementById('viewToggleBtn');
        if (btn) {
            btn.innerHTML = this.viewMode === 'topics' ? '📊 Topics' : '👥 Speakers';
        }
        
        // Re-render if we have data
        if (this.data.threads.length > 0) {
            this.renderer.render(
                this.data.threads,
                this.data.tangents,
                this.data.speakers,
                this.data.totalDuration,
                this.viewMode
            );
            
            // Show elements immediately since we're toggling (no animation needed)
            if (this.viewMode === 'topics') {
                this.showAllNodesImmediately();
            }
            // Speaker view nodes already have opacity: 1 in their inline styles
        }
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
        this.analyticsPanel.clear();
        this.analyticsPanel.toggle(false);

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
     * Generate a conversation using LLM
     * @param {Object} options - Generation options
     */
    async generateConversation(options = {}) {
        try {
            UIFeedback.showLoading(true, 'Generating conversation with AI...');
            
            const result = await this.apiClient.generateConversation(options);
            
            const inputEl = document.getElementById(this.options.inputId);
            if (inputEl) {
                inputEl.value = result.text;
            }
            
            UIFeedback.showLoading(false);
            UIFeedback.showMessage(`✓ Generated conversation about: ${result.topic}`, 'success');
            
        } catch (error) {
            UIFeedback.showLoading(false);
            console.error('Generation failed:', error);
            UIFeedback.showMessage(`Generation failed: ${error.message}`, 'error');
        }
    }

    /**
     * Show saved conversations modal
     */
    async showSavedConversations() {
        try {
            UIFeedback.showLoading(true, 'Loading saved conversations...');
            
            const conversations = await this.apiClient.listConversations();
            
            UIFeedback.showLoading(false);
            
            if (conversations.length === 0) {
                UIFeedback.showMessage('No saved conversations found', 'info');
                return;
            }
            
            // Create modal
            this.showConversationPickerModal(conversations);
            
        } catch (error) {
            UIFeedback.showLoading(false);
            console.error('Failed to load conversations:', error);
            UIFeedback.showMessage(`Failed to load: ${error.message}`, 'error');
        }
    }

    /**
     * Show conversation picker modal
     * @param {Array} conversations - List of conversations
     */
    showConversationPickerModal(conversations) {
        // Remove existing modal if present
        const existing = document.getElementById('conversationPickerModal');
        if (existing) existing.remove();
        
        const modal = document.createElement('div');
        modal.id = 'conversationPickerModal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            max-width: 600px;
            max-height: 70vh;
            overflow-y: auto;
            width: 90%;
        `;
        
        content.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="margin: 0; color: #00d4ff;">📂 Saved Conversations</h3>
                <button onclick="this.closest('#conversationPickerModal').remove()" 
                        style="background: none; border: none; color: #888; font-size: 24px; cursor: pointer;">×</button>
            </div>
            <div id="conversationList" style="display: flex; flex-direction: column; gap: 8px;">
                ${conversations.map(conv => `
                    <div class="conversation-item" data-id="${conv.id}" style="
                        background: rgba(0, 0, 0, 0.3);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                        padding: 12px;
                        cursor: pointer;
                        transition: all 0.2s;
                    " onmouseover="this.style.borderColor='rgba(0, 212, 255, 0.5)'" 
                       onmouseout="this.style.borderColor='rgba(255, 255, 255, 0.1)'">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <div style="color: #fff; font-weight: 600;">${conv.title}</div>
                                <div style="color: #888; font-size: 12px; margin-top: 4px;">
                                    ${conv.speaker_count} speakers • ${conv.thread_count} threads • ${formatTime(conv.total_duration)}
                                </div>
                                <div style="color: #666; font-size: 11px; margin-top: 2px;">
                                    ${new Date(conv.created_at).toLocaleString()}
                                </div>
                            </div>
                            <button onclick="event.stopPropagation(); window.deleteConversation(${conv.id})" 
                                    style="background: none; border: none; color: #666; cursor: pointer; padding: 4px;"
                                    title="Delete">🗑️</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Add click handlers for conversation items
        content.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = item.dataset.id;
                this.loadConversation(id);
                modal.remove();
            });
        });
        
        modal.appendChild(content);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        document.body.appendChild(modal);
    }

    /**
     * Load a conversation by ID
     * @param {number} conversationId - Conversation ID
     */
    async loadConversation(conversationId) {
        try {
            UIFeedback.showLoading(true, 'Loading conversation...');
            
            const conversation = await this.apiClient.getConversation(conversationId);
            
            const inputEl = document.getElementById(this.options.inputId);
            if (inputEl) {
                inputEl.value = conversation.text;
            }
            
            UIFeedback.showLoading(false);
            UIFeedback.showMessage(`✓ Loaded: ${conversation.title}`, 'success');
            
            // Fetch and display analytics for the loaded conversation
            this.fetchAnalyticsForConversation(conversationId);
            
        } catch (error) {
            UIFeedback.showLoading(false);
            console.error('Failed to load conversation:', error);
            UIFeedback.showMessage(`Failed to load: ${error.message}`, 'error');
        }
    }

    /**
     * Fetch analytics for an existing conversation
     * @param {number} conversationId - Conversation ID
     */
    async fetchAnalyticsForConversation(conversationId) {
        try {
            const analytics = await this.apiClient.getConversationAnalytics(conversationId);
            
            if (analytics) {
                this.analyticsPanel.toggle(true);
                this.analyticsPanel.render(analytics);
            }
        } catch (error) {
            console.warn('Could not fetch analytics:', error.message);
        }
    }

    /**
     * Extract topics from the current text without full analysis
     */
    async extractTopicsOnly() {
        const inputEl = document.getElementById(this.options.inputId);
        const text = inputEl?.value?.trim();

        if (!text) {
            alert('Please enter conversation text first.');
            return;
        }

        try {
            UIFeedback.showLoading(true, 'Extracting topics...');
            
            const result = await this.apiClient.extractTopics(text);
            
            UIFeedback.showLoading(false);
            
            // Show topics in a modal
            this.showTopicsModal(result.topics);
            
        } catch (error) {
            UIFeedback.showLoading(false);
            console.error('Topic extraction failed:', error);
            UIFeedback.showMessage(`Topic extraction failed: ${error.message}`, 'error');
        }
    }

    /**
     * Show extracted topics in a modal
     * @param {Array} topics - Extracted topics
     */
    showTopicsModal(topics) {
        // Remove existing modal if present
        const existing = document.getElementById('topicsModal');
        if (existing) existing.remove();
        
        const modal = document.createElement('div');
        modal.id = 'topicsModal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 12px;
            padding: 20px;
            max-width: 500px;
            max-height: 70vh;
            overflow-y: auto;
            width: 90%;
        `;
        
        const maxScore = topics.length > 0 ? Math.max(...topics.map(t => t.score)) : 1;
        
        content.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="margin: 0; color: #00d4ff;">🏷️ Extracted Topics (${topics.length})</h3>
                <button onclick="this.closest('#topicsModal').remove()" 
                        style="background: none; border: none; color: #888; font-size: 24px; cursor: pointer;">×</button>
            </div>
            <p style="color: #888; font-size: 12px; margin-bottom: 16px;">
                Topics are dynamically extracted using NLTK-based NLP analysis including noun phrase extraction, 
                TF-IDF scoring, and named entity recognition.
            </p>
            <div style="display: flex; flex-direction: column; gap: 12px;">
                ${topics.map((topic, i) => {
                    const barWidth = (topic.score / maxScore) * 100;
                    const color = ['#00d4ff', '#ff6b6b', '#00ff88', '#ffd93d', '#ff8cc8'][i % 5];
                    return `
                        <div style="background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 12px; border-left: 3px solid ${color};">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span style="color: #fff; font-weight: 600;">${topic.name}</span>
                                <span style="color: #666; font-size: 11px;">${topic.score.toFixed(1)} score</span>
                            </div>
                            <div style="height: 4px; background: #333; border-radius: 2px; overflow: hidden; margin-bottom: 6px;">
                                <div style="width: ${barWidth}%; height: 100%; background: ${color};"></div>
                            </div>
                            <div style="color: #888; font-size: 11px;">
                                Keywords: ${topic.keywords.slice(0, 5).join(', ')}
                            </div>
                            <div style="color: #666; font-size: 10px; margin-top: 4px;">
                                Sources: ${topic.sources.join(', ')}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
        
        modal.appendChild(content);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        document.body.appendChild(modal);
    }

    // ============ Collection/Corpus Management ============

    /**
     * Show collections management modal
     */
    async showCollectionsModal() {
        try {
            UIFeedback.showLoading(true, 'Loading collections...');
            
            const collections = await this.apiClient.listCollections();
            
            UIFeedback.showLoading(false);
            
            // Create modal
            this.renderCollectionsModal(collections);
            
        } catch (error) {
            UIFeedback.showLoading(false);
            console.error('Failed to load collections:', error);
            UIFeedback.showMessage(`Failed to load collections: ${error.message}`, 'error');
        }
    }

    /**
     * Render the collections modal
     */
    renderCollectionsModal(collections) {
        const existing = document.getElementById('collectionsModal');
        if (existing) existing.remove();
        
        const modal = document.createElement('div');
        modal.id = 'collectionsModal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            padding: 20px;
            max-width: 700px;
            max-height: 80vh;
            overflow-y: auto;
            width: 95%;
        `;
        
        content.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="margin: 0; color: #6366f1;">📚 Collections (Corpus Analysis)</h3>
                <button onclick="this.closest('#collectionsModal').remove()" 
                        style="background: none; border: none; color: #888; font-size: 24px; cursor: pointer;">×</button>
            </div>
            <p style="color: #888; font-size: 12px; margin-bottom: 16px;">
                Collections group conversations for aggregated corpus-level analysis. 
                Compare sentiment, vocabulary, and speaker patterns across multiple conversations.
            </p>
            
            <div style="display: flex; gap: 10px; margin-bottom: 16px;">
                <button id="newCollectionBtn" style="
                    background: linear-gradient(135deg, #6366f1, #4f46e5);
                    border: none;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                ">+ New Collection</button>
            </div>
            
            <div id="collectionsList" style="display: flex; flex-direction: column; gap: 12px;">
                ${collections.length === 0 ? `
                    <div style="text-align: center; color: #666; padding: 40px;">
                        No collections yet. Create one to start grouping conversations.
                    </div>
                ` : collections.map(coll => `
                    <div class="collection-item" data-id="${coll.id}" style="
                        background: rgba(0, 0, 0, 0.3);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                        padding: 16px;
                        cursor: pointer;
                        transition: all 0.2s;
                    " onmouseover="this.style.borderColor='rgba(99, 102, 241, 0.5)'" 
                       onmouseout="this.style.borderColor='rgba(255, 255, 255, 0.1)'">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <div style="color: #fff; font-weight: 600; font-size: 16px;">${coll.name}</div>
                                ${coll.description ? `<div style="color: #888; font-size: 12px; margin-top: 4px;">${coll.description}</div>` : ''}
                                <div style="display: flex; gap: 16px; margin-top: 8px; font-size: 12px;">
                                    <span style="color: #6366f1;">📝 ${coll.conversation_count} conversations</span>
                                    <span style="color: #00d4ff;">💬 ${coll.total_messages} messages</span>
                                    <span style="color: #00ff88;">📊 ${coll.total_words} words</span>
                                    <span style="color: ${coll.avg_sentiment_compound >= 0.05 ? '#00ff88' : coll.avg_sentiment_compound <= -0.05 ? '#ff6b6b' : '#ffd93d'};">
                                        ${coll.avg_sentiment_compound >= 0.05 ? '😊' : coll.avg_sentiment_compound <= -0.05 ? '😔' : '😐'} 
                                        ${coll.avg_sentiment_compound.toFixed(3)}
                                    </span>
                                </div>
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <button class="view-analytics-btn" data-id="${coll.id}" style="
                                    background: linear-gradient(135deg, #22c55e, #16a34a);
                                    border: none;
                                    color: white;
                                    padding: 6px 12px;
                                    border-radius: 4px;
                                    cursor: pointer;
                                    font-size: 11px;
                                ">📊 Analytics</button>
                                <button class="edit-collection-btn" data-id="${coll.id}" style="
                                    background: linear-gradient(135deg, #3b82f6, #2563eb);
                                    border: none;
                                    color: white;
                                    padding: 6px 12px;
                                    border-radius: 4px;
                                    cursor: pointer;
                                    font-size: 11px;
                                ">✏️ Edit</button>
                                <button class="delete-collection-btn" data-id="${coll.id}" style="
                                    background: none;
                                    border: none;
                                    color: #666;
                                    cursor: pointer;
                                    padding: 4px;
                                " title="Delete">🗑️</button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        modal.appendChild(content);
        
        // Event handlers
        content.querySelector('#newCollectionBtn')?.addEventListener('click', () => {
            modal.remove();
            this.showCreateCollectionModal();
        });
        
        content.querySelectorAll('.view-analytics-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = btn.dataset.id;
                modal.remove();
                this.showCollectionAnalytics(id);
            });
        });
        
        content.querySelectorAll('.edit-collection-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = btn.dataset.id;
                modal.remove();
                this.showEditCollectionModal(id);
            });
        });
        
        content.querySelectorAll('.delete-collection-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (confirm('Delete this collection? (Conversations will not be deleted)')) {
                    const id = btn.dataset.id;
                    await this.apiClient.deleteCollection(id);
                    modal.remove();
                    this.showCollectionsModal();
                    UIFeedback.showMessage('✓ Collection deleted', 'success');
                }
            });
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        document.body.appendChild(modal);
    }

    /**
     * Show create collection modal
     */
    async showCreateCollectionModal() {
        const conversations = await this.apiClient.listConversations();
        
        const modal = document.createElement('div');
        modal.id = 'createCollectionModal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            padding: 20px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            width: 95%;
        `;
        
        content.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="margin: 0; color: #6366f1;">➕ Create Collection</h3>
                <button onclick="this.closest('#createCollectionModal').remove()" 
                        style="background: none; border: none; color: #888; font-size: 24px; cursor: pointer;">×</button>
            </div>
            
            <div style="margin-bottom: 16px;">
                <label style="display: block; color: #aaa; font-size: 12px; margin-bottom: 4px;">Name *</label>
                <input type="text" id="collectionName" placeholder="e.g., Marketing Discussions" style="
                    width: 100%;
                    padding: 10px;
                    background: rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: white;
                    font-size: 14px;
                ">
            </div>
            
            <div style="margin-bottom: 16px;">
                <label style="display: block; color: #aaa; font-size: 12px; margin-bottom: 4px;">Description</label>
                <textarea id="collectionDesc" placeholder="Optional description..." rows="2" style="
                    width: 100%;
                    padding: 10px;
                    background: rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: white;
                    font-size: 14px;
                    resize: vertical;
                "></textarea>
            </div>
            
            <div style="margin-bottom: 16px;">
                <label style="display: block; color: #aaa; font-size: 12px; margin-bottom: 8px;">Select Conversations</label>
                <div id="conversationCheckboxes" style="max-height: 200px; overflow-y: auto; background: rgba(0,0,0,0.2); border-radius: 6px; padding: 10px;">
                    ${conversations.length === 0 ? `
                        <div style="color: #666; text-align: center; padding: 20px;">No conversations available</div>
                    ` : conversations.map(conv => `
                        <label style="display: flex; align-items: center; gap: 8px; padding: 6px; cursor: pointer; border-radius: 4px; transition: background 0.2s;"
                               onmouseover="this.style.background='rgba(255,255,255,0.05)'"
                               onmouseout="this.style.background='transparent'">
                            <input type="checkbox" value="${conv.id}" style="cursor: pointer;">
                            <span style="color: #fff; flex: 1;">${conv.title}</span>
                            <span style="color: #666; font-size: 11px;">${conv.speaker_count} speakers</span>
                        </label>
                    `).join('')}
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button onclick="this.closest('#createCollectionModal').remove()" style="
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                ">Cancel</button>
                <button id="createCollectionSubmit" style="
                    background: linear-gradient(135deg, #6366f1, #4f46e5);
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                ">Create Collection</button>
            </div>
        `;
        
        modal.appendChild(content);
        
        content.querySelector('#createCollectionSubmit').addEventListener('click', async () => {
            const name = content.querySelector('#collectionName').value.trim();
            const description = content.querySelector('#collectionDesc').value.trim();
            const checkboxes = content.querySelectorAll('#conversationCheckboxes input:checked');
            const conversationIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
            
            if (!name) {
                alert('Please enter a collection name');
                return;
            }
            
            try {
                await this.apiClient.createCollection({
                    name,
                    description: description || null,
                    conversation_ids: conversationIds
                });
                
                modal.remove();
                UIFeedback.showMessage('✓ Collection created', 'success');
                this.showCollectionsModal();
            } catch (error) {
                UIFeedback.showMessage(`Failed: ${error.message}`, 'error');
            }
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        document.body.appendChild(modal);
    }

    /**
     * Show edit collection modal
     */
    async showEditCollectionModal(collectionId) {
        const [collection, conversations] = await Promise.all([
            this.apiClient.getCollection(collectionId),
            this.apiClient.listConversations()
        ]);
        
        const modal = document.createElement('div');
        modal.id = 'editCollectionModal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            padding: 20px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            width: 95%;
        `;
        
        content.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="margin: 0; color: #6366f1;">✏️ Edit Collection</h3>
                <button onclick="this.closest('#editCollectionModal').remove()" 
                        style="background: none; border: none; color: #888; font-size: 24px; cursor: pointer;">×</button>
            </div>
            
            <div style="margin-bottom: 16px;">
                <label style="display: block; color: #aaa; font-size: 12px; margin-bottom: 4px;">Name *</label>
                <input type="text" id="editCollectionName" value="${collection.name}" style="
                    width: 100%;
                    padding: 10px;
                    background: rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: white;
                    font-size: 14px;
                ">
            </div>
            
            <div style="margin-bottom: 16px;">
                <label style="display: block; color: #aaa; font-size: 12px; margin-bottom: 4px;">Description</label>
                <textarea id="editCollectionDesc" rows="2" style="
                    width: 100%;
                    padding: 10px;
                    background: rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: white;
                    font-size: 14px;
                    resize: vertical;
                ">${collection.description || ''}</textarea>
            </div>
            
            <div style="margin-bottom: 16px;">
                <label style="display: block; color: #aaa; font-size: 12px; margin-bottom: 8px;">Conversations in Collection</label>
                <div id="editConversationCheckboxes" style="max-height: 200px; overflow-y: auto; background: rgba(0,0,0,0.2); border-radius: 6px; padding: 10px;">
                    ${conversations.map(conv => `
                        <label style="display: flex; align-items: center; gap: 8px; padding: 6px; cursor: pointer;">
                            <input type="checkbox" value="${conv.id}" 
                                   ${collection.conversation_ids.includes(conv.id) ? 'checked' : ''}>
                            <span style="color: #fff; flex: 1;">${conv.title}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button onclick="this.closest('#editCollectionModal').remove()" style="
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                ">Cancel</button>
                <button id="saveCollectionBtn" style="
                    background: linear-gradient(135deg, #6366f1, #4f46e5);
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 600;
                ">Save Changes</button>
            </div>
        `;
        
        modal.appendChild(content);
        
        content.querySelector('#saveCollectionBtn').addEventListener('click', async () => {
            const name = content.querySelector('#editCollectionName').value.trim();
            const description = content.querySelector('#editCollectionDesc').value.trim();
            const checkboxes = content.querySelectorAll('#editConversationCheckboxes input:checked');
            const conversationIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
            
            if (!name) {
                alert('Please enter a collection name');
                return;
            }
            
            try {
                await this.apiClient.updateCollection(collectionId, {
                    name,
                    description: description || null,
                    conversation_ids: conversationIds
                });
                
                modal.remove();
                UIFeedback.showMessage('✓ Collection updated', 'success');
                this.showCollectionsModal();
            } catch (error) {
                UIFeedback.showMessage(`Failed: ${error.message}`, 'error');
            }
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        document.body.appendChild(modal);
    }

    /**
     * Show collection analytics modal
     */
    async showCollectionAnalytics(collectionId) {
        try {
            UIFeedback.showLoading(true, 'Analyzing collection...');
            
            const analytics = await this.apiClient.getCollectionAnalytics(collectionId);
            
            UIFeedback.showLoading(false);
            
            this.renderCollectionAnalyticsModal(analytics);
            
        } catch (error) {
            UIFeedback.showLoading(false);
            console.error('Failed to get collection analytics:', error);
            UIFeedback.showMessage(`Failed: ${error.message}`, 'error');
        }
    }

    /**
     * Render collection analytics modal
     */
    renderCollectionAnalyticsModal(analytics) {
        const modal = document.createElement('div');
        modal.id = 'collectionAnalyticsModal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const sentimentColor = analytics.overall_sentiment === 'positive' ? '#00ff88' : 
                              analytics.overall_sentiment === 'negative' ? '#ff6b6b' : '#ffd93d';
        const sentimentEmoji = analytics.overall_sentiment === 'positive' ? '😊' : 
                              analytics.overall_sentiment === 'negative' ? '😔' : '😐';
        
        const content = document.createElement('div');
        content.style.cssText = `
            background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            padding: 24px;
            max-width: 900px;
            max-height: 90vh;
            overflow-y: auto;
            width: 95%;
        `;
        
        content.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #6366f1;">📊 ${analytics.collection_name} - Corpus Analytics</h3>
                <button onclick="this.closest('#collectionAnalyticsModal').remove()" 
                        style="background: none; border: none; color: #888; font-size: 24px; cursor: pointer;">×</button>
            </div>
            
            <!-- Overview Stats -->
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 24px;">
                <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 16px; text-align: center;">
                    <div style="font-size: 28px; font-weight: 700; color: #6366f1;">${analytics.conversation_count}</div>
                    <div style="font-size: 11px; color: #888;">Conversations</div>
                </div>
                <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 16px; text-align: center;">
                    <div style="font-size: 28px; font-weight: 700; color: #00d4ff;">${analytics.total_messages}</div>
                    <div style="font-size: 11px; color: #888;">Total Messages</div>
                </div>
                <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 16px; text-align: center;">
                    <div style="font-size: 28px; font-weight: 700; color: #00ff88;">${analytics.total_words}</div>
                    <div style="font-size: 11px; color: #888;">Total Words</div>
                </div>
                <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 16px; text-align: center;">
                    <div style="font-size: 28px; font-weight: 700; color: #ffd93d;">${analytics.unique_speakers}</div>
                    <div style="font-size: 11px; color: #888;">Unique Speakers</div>
                </div>
                <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 16px; text-align: center;">
                    <div style="font-size: 28px; font-weight: 700; color: ${sentimentColor};">${sentimentEmoji}</div>
                    <div style="font-size: 11px; color: #888;">${analytics.overall_sentiment}</div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px;">
                <!-- Sentiment Distribution -->
                <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 16px;">
                    <h4 style="margin: 0 0 12px 0; color: #00d4ff; font-size: 14px;">📉 Sentiment Distribution</h4>
                    <div style="display: flex; gap: 8px; height: 20px; margin-bottom: 12px;">
                        ${analytics.sentiment_distribution.positive > 0 ? `
                            <div style="background: #00ff88; flex: ${analytics.sentiment_distribution.positive}; border-radius: 4px;"></div>
                        ` : ''}
                        ${analytics.sentiment_distribution.neutral > 0 ? `
                            <div style="background: #ffd93d; flex: ${analytics.sentiment_distribution.neutral}; border-radius: 4px;"></div>
                        ` : ''}
                        ${analytics.sentiment_distribution.negative > 0 ? `
                            <div style="background: #ff6b6b; flex: ${analytics.sentiment_distribution.negative}; border-radius: 4px;"></div>
                        ` : ''}
                    </div>
                    <div style="display: flex; justify-content: space-around; font-size: 12px;">
                        <span style="color: #00ff88;">😊 ${analytics.sentiment_distribution.positive} positive</span>
                        <span style="color: #ffd93d;">😐 ${analytics.sentiment_distribution.neutral} neutral</span>
                        <span style="color: #ff6b6b;">😔 ${analytics.sentiment_distribution.negative} negative</span>
                    </div>
                </div>
                
                <!-- Top Words -->
                <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 16px;">
                    <h4 style="margin: 0 0 12px 0; color: #00d4ff; font-size: 14px;">🔤 Top Words Across Corpus</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                        ${analytics.word_frequency.slice(0, 15).map((wf, i) => `
                            <span style="
                                background: rgba(99, 102, 241, ${0.8 - i * 0.05});
                                padding: 4px 8px;
                                border-radius: 4px;
                                font-size: 11px;
                                color: white;
                            ">${wf.word} (${wf.count})</span>
                        `).join('')}
                    </div>
                </div>
            </div>
            
            <!-- Common Topics -->
            ${analytics.common_topics && analytics.common_topics.length > 0 ? `
                <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                    <h4 style="margin: 0 0 12px 0; color: #00d4ff; font-size: 14px;">🏷️ Common Topics</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                        ${analytics.common_topics.slice(0, 8).map(topic => `
                            <div style="background: rgba(99, 102, 241, 0.2); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 6px; padding: 8px 12px;">
                                <div style="color: #fff; font-weight: 600; font-size: 13px;">${topic.topic}</div>
                                <div style="color: #888; font-size: 10px;">
                                    ${topic.count} convs (${topic.percentage.toFixed(0)}%)
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            <!-- Conversation Comparison -->
            <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #00d4ff; font-size: 14px;">📋 Conversation Comparison</h4>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                                <th style="text-align: left; padding: 8px; color: #888;">Title</th>
                                <th style="text-align: right; padding: 8px; color: #888;">Messages</th>
                                <th style="text-align: right; padding: 8px; color: #888;">Words</th>
                                <th style="text-align: center; padding: 8px; color: #888;">Sentiment</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${analytics.conversation_summaries.map(conv => `
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                                    <td style="padding: 8px; color: #fff;">${conv.title}</td>
                                    <td style="padding: 8px; color: #00d4ff; text-align: right;">${conv.messages}</td>
                                    <td style="padding: 8px; color: #00ff88; text-align: right;">${conv.words}</td>
                                    <td style="padding: 8px; text-align: center; color: ${
                                        conv.sentiment === 'positive' ? '#00ff88' : 
                                        conv.sentiment === 'negative' ? '#ff6b6b' : '#ffd93d'
                                    };">
                                        ${conv.sentiment === 'positive' ? '😊' : conv.sentiment === 'negative' ? '😔' : '😐'}
                                        ${conv.compound.toFixed(3)}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div style="margin-top: 16px; text-align: center;">
                <button onclick="this.closest('#collectionAnalyticsModal').remove()" style="
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    color: white;
                    padding: 10px 30px;
                    border-radius: 6px;
                    cursor: pointer;
                ">Close</button>
            </div>
        `;
        
        modal.appendChild(content);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        document.body.appendChild(modal);
    }

    /**
     * Delete a conversation
     * @param {number} conversationId - Conversation ID
     */
    async deleteConversation(conversationId) {
        if (!confirm('Are you sure you want to delete this conversation?')) {
            return;
        }
        
        try {
            await this.apiClient.deleteConversation(conversationId);
            
            // Refresh the modal
            const modal = document.getElementById('conversationPickerModal');
            if (modal) {
                modal.remove();
                this.showSavedConversations();
            }
            
            UIFeedback.showMessage('✓ Conversation deleted', 'success');
            
        } catch (error) {
            console.error('Failed to delete conversation:', error);
            UIFeedback.showMessage(`Failed to delete: ${error.message}`, 'error');
        }
    }

    /**
     * Export database to file
     */
    async exportDatabase() {
        try {
            UIFeedback.showLoading(true, 'Exporting database...');
            
            const data = await this.apiClient.exportDatabase();
            
            // Create download
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `looksatwords_export_${new Date().toISOString().slice(0,10)}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            UIFeedback.showLoading(false);
            UIFeedback.showMessage(`✓ Exported ${data.conversations.length} conversations`, 'success');
            
        } catch (error) {
            UIFeedback.showLoading(false);
            console.error('Export failed:', error);
            UIFeedback.showMessage(`Export failed: ${error.message}`, 'error');
        }
    }

    /**
     * Import database from file
     */
    async importDatabase() {
        // Create file input
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            try {
                UIFeedback.showLoading(true, 'Reading file...');
                
                const text = await file.text();
                const data = JSON.parse(text);
                
                // Ask for import mode
                const mode = confirm('Click OK to merge with existing data, or Cancel to replace all data') 
                    ? 'merge' 
                    : 'replace';
                
                if (mode === 'replace' && !confirm('This will DELETE all existing conversations. Are you sure?')) {
                    UIFeedback.showLoading(false);
                    return;
                }
                
                UIFeedback.showLoading(true, 'Importing...');
                
                const result = await this.apiClient.importDatabase(data, mode);
                
                UIFeedback.showLoading(false);
                UIFeedback.showMessage(
                    `✓ Imported ${result.imported} conversations (${result.skipped} skipped)`, 
                    'success'
                );
                
            } catch (error) {
                UIFeedback.showLoading(false);
                console.error('Import failed:', error);
                UIFeedback.showMessage(`Import failed: ${error.message}`, 'error');
            }
        };
        
        input.click();
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

window.generateConversation = async function() {
    await getApp().generateConversation();
};

window.showSavedConversations = async function() {
    await getApp().showSavedConversations();
};

window.deleteConversation = async function(id) {
    await getApp().deleteConversation(id);
};

window.exportDatabase = async function() {
    await getApp().exportDatabase();
};

window.importDatabase = async function() {
    await getApp().importDatabase();
};

window.toggleViewMode = function() {
    getApp().toggleViewMode();
};

window.extractTopics = async function() {
    await getApp().extractTopicsOnly();
};

window.showCollections = async function() {
    await getApp().showCollectionsModal();
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    getApp();
});

// Export for module usage
export { getApp };
