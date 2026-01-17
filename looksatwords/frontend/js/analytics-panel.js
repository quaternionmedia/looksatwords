/**
 * Analytics Panel Module
 * Bottom slide-up panel with tabs for Analytics, Charts, News, I/O, and Collections
 */

import { CONFIG } from './config.js';
import { formatTime } from './models.js';

/**
 * Analytics panel renderer - slides up from bottom with tabbed interface
 */
export class AnalyticsPanel {
    constructor(containerId = 'analyticsPanel') {
        this.containerId = containerId;
        this.panel = null;
        this.resizeBar = null;
        this.container = null;
        this.tabsContainer = null;
        this.isVisible = false;
        this.hasData = false;
        this.analyticsData = null;
        this.currentTab = 'analytics';
        
        // External dependencies (set by app.js)
        this.apiClient = null;
        this.conversationId = null;
        
        // Callback for loading conversations (set by app.js)
        this.onLoadConversation = null;
        
        // Panel height
        this.panelHeight = 360;
        this.minHeight = 200;
        this.maxHeight = window.innerHeight - 150;
        this.isResizing = false;
        
        // Tab definitions
        this.tabs = [
            { id: 'analytics', label: 'Analytics', icon: '📊' },
            { id: 'charts', label: 'Charts', icon: '📈' },
            { id: 'news', label: 'News', icon: '📰' },
            { id: 'io', label: 'I/O', icon: '💾' },
            { id: 'collections', label: 'Collections', icon: '📚' }
        ];
        
        // Initialize immediately if DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Set API client reference
     */
    setApiClient(apiClient) {
        this.apiClient = apiClient;
    }

    /**
     * Set current conversation ID
     */
    setConversationId(id) {
        this.conversationId = id;
        // If charts tab is active, refresh it
        if (this.currentTab === 'charts' && this.isVisible) {
            this.renderChartsTab();
        }
    }

    /**
     * Initialize the panel
     */
    init() {
        this.panel = document.getElementById(this.containerId);
        if (!this.panel) {
            this.createPanel();
        }
        this.setupResizeBar();
    }

    /**
     * Create panel DOM structure
     */
    createPanel() {
        this.panel = document.createElement('div');
        this.panel.id = this.containerId;
        this.panel.className = 'analytics-slide-panel';
        this.panel.innerHTML = `
            <div class="analytics-resize-bar" title="Drag to resize">
                <span class="resize-handle"></span>
            </div>
            <div class="analytics-tabs"></div>
            <div class="analytics-content-scroll">
                <div class="analytics-content"></div>
            </div>
        `;
        document.body.appendChild(this.panel);
        
        this.tabsContainer = this.panel.querySelector('.analytics-tabs');
        this.container = this.panel.querySelector('.analytics-content');
        this.resizeBar = this.panel.querySelector('.analytics-resize-bar');
        
        this.renderTabs();
    }

    /**
     * Render tab buttons
     */
    renderTabs() {
        this.tabsContainer.innerHTML = this.tabs.map(tab => `
            <button class="analytics-tab ${tab.id === this.currentTab ? 'active' : ''}" 
                    data-tab="${tab.id}">
                <span class="analytics-tab-icon">${tab.icon}</span>
                <span class="analytics-tab-label">${tab.label}</span>
            </button>
        `).join('');
        
        // Add click handlers
        this.tabsContainer.querySelectorAll('.analytics-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                this.switchTab(tabId);
            });
        });
    }

    /**
     * Switch to a tab
     */
    switchTab(tabId) {
        this.currentTab = tabId;
        
        // Update tab button styles
        this.tabsContainer.querySelectorAll('.analytics-tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        
        // Render tab content
        this.renderCurrentTab();
    }

    /**
     * Open panel to a specific tab
     */
    openToTab(tabId) {
        this.show();
        this.switchTab(tabId);
    }

    /**
     * Setup resize functionality
     */
    setupResizeBar() {
        if (!this.resizeBar) return;
        
        let startY, startHeight;
        
        const onMouseMove = (e) => {
            if (!this.isResizing) return;
            const delta = startY - e.clientY;
            const newHeight = Math.min(this.maxHeight, Math.max(this.minHeight, startHeight + delta));
            this.panelHeight = newHeight;
            this.panel.style.height = `${newHeight}px`;
        };
        
        const onMouseUp = () => {
            this.isResizing = false;
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
        
        this.resizeBar.addEventListener('mousedown', (e) => {
            this.isResizing = true;
            startY = e.clientY;
            startHeight = this.panelHeight;
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            document.body.style.cursor = 'ns-resize';
            document.body.style.userSelect = 'none';
        });
    }

    /**
     * Show the panel
     */
    show() {
        if (!this.panel) this.init();
        this.panel.style.height = `${this.panelHeight}px`;
        this.panel.classList.add('visible');
        this.isVisible = true;
    }

    /**
     * Hide the panel
     */
    hide() {
        if (this.panel) {
            this.panel.classList.remove('visible');
            this.isVisible = false;
        }
    }

    /**
     * Toggle panel visibility
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * Update analytics data and show panel
     */
    update(analyticsData) {
        this.analyticsData = analyticsData;
        this.hasData = true;
        this.renderCurrentTab();
        this.show();
    }

    /**
     * Clear analytics data
     */
    clear() {
        this.analyticsData = null;
        this.conversationId = null;
        this.hasData = false;
        if (this.container) {
            this.container.innerHTML = '';
        }
    }

    /**
     * Render current tab content
     */
    renderCurrentTab() {
        if (!this.container) return;
        this.container.innerHTML = '';
        
        switch (this.currentTab) {
            case 'analytics':
                this.renderAnalyticsTab();
                break;
            case 'charts':
                this.renderChartsTab();
                break;
            case 'news':
                this.renderNewsTab();
                break;
            case 'io':
                this.renderIOTab();
                break;
            case 'collections':
                this.renderCollectionsTab();
                break;
        }
    }

    // ==================== ANALYTICS TAB ====================
    
    renderAnalyticsTab() {
        if (!this.analyticsData) {
            this.container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📊</div>
                    <div class="empty-state-text">No analytics data available</div>
                    <div style="font-size: 12px; margin-top: 8px; color: #555;">Analyze a conversation to see analytics here</div>
                </div>
            `;
            return;
        }
        
        // Create horizontal layout for all content
        const contentWrapper = document.createElement('div');
        contentWrapper.style.cssText = `
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            align-items: flex-start;
        `;
        
        // Overview card
        if (this.analyticsData.aggregated) {
            contentWrapper.appendChild(this.renderOverviewCard(this.analyticsData.aggregated));
        }
        
        // Sentiment chart
        if (this.analyticsData.sentiment_timeline?.length > 0) {
            contentWrapper.appendChild(this.renderMiniSentimentChart(this.analyticsData.sentiment_timeline));
        }
        
        // Word frequency
        if (this.analyticsData.aggregated?.word_frequency?.length > 0) {
            contentWrapper.appendChild(this.renderWordFrequency(this.analyticsData.aggregated.word_frequency));
        }
        
        // POS distribution
        if (this.analyticsData.aggregated?.pos_distribution) {
            contentWrapper.appendChild(this.renderPOSDistribution(this.analyticsData.aggregated.pos_distribution));
        }
        
        this.container.appendChild(contentWrapper);
        
        // Speaker analytics in separate row
        if (this.analyticsData.speaker_analytics && Object.keys(this.analyticsData.speaker_analytics).length > 0) {
            const speakerWrapper = document.createElement('div');
            speakerWrapper.style.cssText = `margin-top: 16px;`;
            speakerWrapper.appendChild(this.renderSpeakerAnalytics(this.analyticsData.speaker_analytics));
            this.container.appendChild(speakerWrapper);
        }
    }

    // ==================== CHARTS TAB ====================
    
    async renderChartsTab() {
        if (!this.conversationId) {
            this.container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📈</div>
                    <div class="empty-state-text">No conversation loaded</div>
                    <div style="font-size: 12px; margin-top: 8px; color: #555;">Analyze a conversation first to generate charts</div>
                </div>
            `;
            return;
        }
        
        // Show loading
        this.container.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div class="loading-spinner-lg" style="margin: 0 auto 16px;"></div>
                <div style="color: #888;">Generating visualizations...</div>
            </div>
        `;
        
        try {
            const data = await this.apiClient.getConversationVisualizations(this.conversationId);
            this.renderChartsContent(data);
        } catch (error) {
            this.container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <div class="empty-state-text">Failed to load charts</div>
                    <div style="font-size: 12px; margin-top: 8px; color: #888;">${error.message}</div>
                </div>
            `;
        }
    }

    renderChartsContent(data) {
        const visualizations = data.visualizations || {};
        const vizKeys = Object.keys(visualizations);
        
        if (vizKeys.length === 0) {
            this.container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📈</div>
                    <div class="empty-state-text">No visualizations available</div>
                    <div style="font-size: 12px; margin-top: 8px; color: #555;">Make sure matplotlib is installed</div>
                </div>
            `;
            return;
        }
        
        // Clear container first
        this.container.innerHTML = '';
        
        const grid = document.createElement('div');
        grid.style.cssText = `
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 16px;
        `;
        
        const titles = {
            'word_cloud': '☁️ Word Cloud',
            'word_frequency': '📊 Word Frequency',
            'sentiment': '😊 Sentiment Analysis',
            'pos': '🏷️ Parts of Speech',
            'speakers': '👥 Speaker Comparison'
        };
        
        vizKeys.forEach(key => {
            const viz = visualizations[key];
            const card = document.createElement('div');
            card.style.cssText = `
                background: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 12px;
            `;
            
            if (viz.error) {
                card.innerHTML = `
                    <div style="color: #ff6b6b; font-weight: 600; margin-bottom: 8px;">${titles[key] || key}</div>
                    <div style="color: #888; font-size: 12px;">${viz.error}</div>
                `;
            } else if (viz.image_base64) {
                card.innerHTML = `
                    <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 13px;">${titles[key] || key}</div>
                    <img src="data:image/png;base64,${viz.image_base64}" 
                         style="width: 100%; border-radius: 4px; cursor: pointer;"
                         onclick="window.open(this.src, '_blank')"
                         title="Click to open full size">
                `;
            }
            
            grid.appendChild(card);
        });
        
        this.container.appendChild(grid);
    }

    // ==================== NEWS TAB ====================
    
    async renderNewsTab() {
        // Show loading while checking service status
        this.container.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div class="loading-spinner-lg" style="margin: 0 auto 16px;"></div>
                <div style="color: #888;">Checking news services...</div>
            </div>
        `;
        
        // Check service status
        let status = { gnews_available: false, llm_available: false };
        try {
            if (this.apiClient) {
                status = await this.apiClient.getNewsServiceStatus();
            }
        } catch (e) {
            console.error('Failed to check news service status:', e);
        }
        
        this.container.innerHTML = `
            <div class="news-panel-grid">
                <div class="tab-section">
                    <div class="tab-section-title">📰 Gather News</div>
                    <div class="service-status">
                        <span class="status-dot ${status.gnews_available ? 'online' : 'offline'}"></span>
                        <span>GNews API: ${status.gnews_available ? 'Available' : 'Unavailable'}</span>
                    </div>
                    <input type="text" class="tab-input" id="newsQuery" placeholder="Search topic (e.g., AI, climate)...">
                    <select class="tab-select" id="newsCategory">
                        <option value="">Any Category</option>
                        <option value="WORLD">🌍 World</option>
                        <option value="TECHNOLOGY">💻 Technology</option>
                        <option value="BUSINESS">💼 Business</option>
                        <option value="SCIENCE">🔬 Science</option>
                        <option value="HEALTH">🏥 Health</option>
                    </select>
                    <button class="btn btn--sm btn--cyan" id="gatherNewsBtn" 
                        ${!status.gnews_available ? 'disabled' : ''}>📡 Gather</button>
                </div>
                
                <div class="tab-section">
                    <div class="tab-section-title">✨ Generate News</div>
                    <div class="service-status">
                        <span class="status-dot ${status.llm_available ? 'online' : 'offline'}"></span>
                        <span>LLM: ${status.llm_available ? 'Available' : 'Unavailable'}</span>
                    </div>
                    <input type="text" class="tab-input" id="generateTopic" placeholder="Topic to generate (e.g., space exploration)...">
                    <button class="btn btn--sm btn--purple" id="generateNewsBtn"
                        ${!status.llm_available ? 'disabled' : ''}>🤖 Generate</button>
                </div>
            </div>
            
            <div class="tab-section" id="newsResults" style="display: none;">
                <div class="tab-section-title">📋 Results</div>
                <div id="newsResultsList"></div>
            </div>
        `;
        
        // Bind handlers
        this.container.querySelector('#gatherNewsBtn')?.addEventListener('click', () => this.gatherNews());
        this.container.querySelector('#generateNewsBtn')?.addEventListener('click', () => this.generateNews());
    }

    async gatherNews() {
        const query = this.container.querySelector('#newsQuery')?.value?.trim();
        const category = this.container.querySelector('#newsCategory')?.value;
        const btn = this.container.querySelector('#gatherNewsBtn');
        
        if (!query) {
            alert('Please enter a search topic');
            return;
        }
        
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner-sm"></span> Gathering...';
        
        try {
            const params = { keyword: query };
            if (category) params.topic = category;
            const result = await this.apiClient.gatherNews(params);
            this.showNewsResults(result.articles || []);
        } catch (error) {
            alert(`Failed to gather news: ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = '📡 Gather';
        }
    }

    async generateNews() {
        const topic = this.container.querySelector('#generateTopic')?.value?.trim();
        const btn = this.container.querySelector('#generateNewsBtn');
        
        if (!topic) {
            alert('Please enter a topic');
            return;
        }
        
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner-sm"></span> Generating...';
        
        try {
            const result = await this.apiClient.generateNews(topic);
            this.showNewsResults(result.articles || []);
        } catch (error) {
            alert(`Failed to generate news: ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = '🤖 Generate';
        }
    }

    showNewsResults(articles) {
        const resultsDiv = this.container.querySelector('#newsResults');
        const listDiv = this.container.querySelector('#newsResultsList');
        
        if (!articles.length) {
            resultsDiv.style.display = 'none';
            return;
        }
        
        resultsDiv.style.display = 'block';
        listDiv.innerHTML = articles.map(article => `
            <div class="saved-item" style="flex-direction: column; align-items: flex-start;">
                <div class="saved-item-title">${article.title}</div>
                <div class="saved-item-meta" style="display: flex; gap: 12px; margin-top: 4px;">
                    ${article.publisher ? `<span>📰 ${article.publisher}</span>` : ''}
                    <span style="color: ${article.source_type === 'generated' ? '#9333ea' : '#00d4ff'};">
                        ${article.source_type === 'generated' ? '🤖 Generated' : '📡 Gathered'}
                    </span>
                </div>
                ${article.description ? `<div style="font-size: 12px; color: #888; margin-top: 6px;">${article.description}</div>` : ''}
            </div>
        `).join('');
    }

    // ==================== I/O TAB ====================
    
    async renderIOTab() {
        // Show loading first
        this.container.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div class="loading-spinner-lg" style="margin: 0 auto 16px;"></div>
                <div style="color: #888;">Loading saved conversations...</div>
            </div>
        `;
        
        // Fetch conversations
        let conversations = [];
        try {
            if (this.apiClient) {
                conversations = await this.apiClient.listConversations();
            }
        } catch (e) {
            console.error('Failed to load conversations:', e);
        }
        
        this.container.innerHTML = `
            <div class="tab-section">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div class="tab-section-title" style="margin-bottom: 0;">📂 Saved Conversations (${conversations.length})</div>
                    <button class="btn btn--sm btn--cyan" id="refreshConversationsBtn"
                        style="padding: 4px 10px; font-size: 11px;">🔄 Refresh</button>
                </div>
                <div class="saved-list" id="savedConversationsList">
                    ${conversations.length === 0 ? `
                        <div class="empty-state">
                            <div class="empty-state-text">No saved conversations</div>
                        </div>
                    ` : conversations.map(conv => `
                        <div class="saved-item" data-id="${conv.id}">
                            <div class="saved-item-info">
                                <div class="saved-item-title">${conv.title || `Conversation ${conv.id}`}</div>
                                <div class="saved-item-meta">${conv.message_count || 0} messages • ${new Date(conv.created_at).toLocaleDateString()}</div>
                            </div>
                            <div class="saved-item-actions">
                                <button class="btn btn--sm btn--red delete-conv-btn" data-id="${conv.id}"
                                    style="padding: 4px 8px; font-size: 11px;" title="Delete">🗑️</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="tab-section">
                <div class="tab-section-title">💾 Database Operations</div>
                <div class="io-actions">
                    <button class="btn btn--sm btn--teal" id="exportDbBtn"
                        style="flex: 1;">📤 Export Database</button>
                    <button class="btn btn--sm btn--pink" id="importDbBtn"
                        style="flex: 1;">📥 Import Database</button>
                </div>
            </div>
        `;
        
        // Bind handlers
        this.container.querySelector('#refreshConversationsBtn')?.addEventListener('click', () => this.renderIOTab());
        this.container.querySelector('#exportDbBtn')?.addEventListener('click', () => this.exportDatabase());
        this.container.querySelector('#importDbBtn')?.addEventListener('click', () => this.importDatabase());
        
        // Conversation click handlers
        this.container.querySelectorAll('.saved-item[data-id]').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.delete-conv-btn')) {
                    const id = item.dataset.id;
                    if (this.onLoadConversation) {
                        this.onLoadConversation(parseInt(id));
                    }
                }
            });
        });
        
        // Delete handlers
        this.container.querySelectorAll('.delete-conv-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.dataset.id;
                if (confirm('Delete this conversation?')) {
                    try {
                        await this.apiClient.deleteConversation(id);
                        this.renderIOTab();
                    } catch (error) {
                        alert(`Failed to delete: ${error.message}`);
                    }
                }
            });
        });
    }

    async exportDatabase() {
        const btn = this.container.querySelector('#exportDbBtn');
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner-sm"></span> Exporting...';
        
        try {
            const data = await this.apiClient.exportDatabase();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `looksatwords-export-${new Date().toISOString().slice(0,10)}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            alert(`Export failed: ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = '📤 Export Database';
        }
    }

    async importDatabase() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const btn = this.container.querySelector('#importDbBtn');
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner-sm"></span> Importing...';
            
            try {
                const text = await file.text();
                const data = JSON.parse(text);
                await this.apiClient.importDatabase(data);
                alert('Import successful!');
                this.renderIOTab();
            } catch (error) {
                alert(`Import failed: ${error.message}`);
            } finally {
                btn.disabled = false;
                btn.textContent = '📥 Import Database';
            }
        };
        
        input.click();
    }

    // ==================== COLLECTIONS TAB ====================
    
    async renderCollectionsTab() {
        // Show loading
        this.container.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div class="loading-spinner-lg" style="margin: 0 auto 16px;"></div>
                <div style="color: #888;">Loading collections...</div>
            </div>
        `;
        
        // Fetch collections
        let collections = [];
        try {
            if (this.apiClient) {
                collections = await this.apiClient.listCollections();
            }
        } catch (e) {
            console.error('Failed to load collections:', e);
        }
        
        this.container.innerHTML = `
            <div class="tab-section">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div class="tab-section-title" style="margin-bottom: 0;">📚 Collections (${collections.length})</div>
                    <button class="btn btn--sm btn--purple" id="createCollectionBtn"
                        style="padding: 4px 10px; font-size: 11px;">+ New Collection</button>
                </div>
                
                <div id="newCollectionForm" style="display: none; margin-bottom: 16px;">
                    <input type="text" class="tab-input" id="newCollectionName" placeholder="Collection name...">
                    <input type="text" class="tab-input" id="newCollectionDesc" placeholder="Description (optional)...">
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn--sm btn--green" id="saveNewCollectionBtn">Create</button>
                        <button class="btn btn--sm btn--gray" id="cancelNewCollectionBtn">Cancel</button>
                    </div>
                </div>
                
                <div class="collections-grid" id="collectionsGrid">
                    ${collections.length === 0 ? `
                        <div class="empty-state" style="grid-column: 1/-1;">
                            <div class="empty-state-icon">📚</div>
                            <div class="empty-state-text">No collections yet</div>
                            <div style="font-size: 12px; margin-top: 8px; color: #555;">Create a collection to organize conversations</div>
                        </div>
                    ` : collections.map(coll => `
                        <div class="collection-card" data-id="${coll.id}">
                            <div class="collection-name">${coll.name}</div>
                            <div class="collection-count">
                                <div style="display: flex; gap: 8px; flex-wrap: wrap; font-size: 11px;">
                                    <span style="color: #6366f1;">📁 ${coll.conversation_count} convs</span>
                                    <span style="color: #00d4ff;">💬 ${coll.total_messages} msgs</span>
                                    ${coll.avg_sentiment_compound !== undefined ? `
                                        <span>${coll.avg_sentiment_compound >= 0.05 ? '😊' : coll.avg_sentiment_compound <= -0.05 ? '😞' : '😐'} 
                                        ${(coll.avg_sentiment_compound * 100).toFixed(0)}%</span>
                                    ` : ''}
                                </div>
                            </div>
                            <div style="display: flex; gap: 6px; margin-top: 8px;">
                                <button class="btn btn--sm btn--cyan view-collection-btn" data-id="${coll.id}"
                                    style="padding: 2px 8px; font-size: 10px;">📊</button>
                                <button class="btn btn--sm btn--yellow edit-collection-btn" data-id="${coll.id}"
                                    style="padding: 2px 8px; font-size: 10px;">✏️</button>
                                <button class="btn btn--sm btn--red delete-collection-btn" data-id="${coll.id}"
                                    style="padding: 2px 8px; font-size: 10px;" title="Delete">🗑️</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div id="collectionDetail" style="display: none;"></div>
        `;
        
        // Bind handlers
        this.container.querySelector('#createCollectionBtn')?.addEventListener('click', () => {
            this.container.querySelector('#newCollectionForm').style.display = 'block';
        });
        
        this.container.querySelector('#cancelNewCollectionBtn')?.addEventListener('click', () => {
            this.container.querySelector('#newCollectionForm').style.display = 'none';
        });
        
        this.container.querySelector('#saveNewCollectionBtn')?.addEventListener('click', () => this.createCollection());
        
        // Collection action handlers
        this.container.querySelectorAll('.view-collection-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.viewCollectionAnalytics(btn.dataset.id);
            });
        });
        
        this.container.querySelectorAll('.edit-collection-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.editCollection(btn.dataset.id);
            });
        });
        
        this.container.querySelectorAll('.delete-collection-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (confirm('Delete this collection?')) {
                    try {
                        await this.apiClient.deleteCollection(btn.dataset.id);
                        this.renderCollectionsTab();
                    } catch (error) {
                        alert(`Failed to delete: ${error.message}`);
                    }
                }
            });
        });
    }

    async createCollection() {
        const name = this.container.querySelector('#newCollectionName')?.value?.trim();
        const description = this.container.querySelector('#newCollectionDesc')?.value?.trim();
        
        if (!name) {
            alert('Please enter a collection name');
            return;
        }
        
        try {
            await this.apiClient.createCollection({ name, description });
            this.renderCollectionsTab();
        } catch (error) {
            alert(`Failed to create collection: ${error.message}`);
        }
    }

    async viewCollectionAnalytics(collectionId) {
        const detailDiv = this.container.querySelector('#collectionDetail');
        detailDiv.style.display = 'block';
        detailDiv.innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <div class="loading-spinner-lg" style="margin: 0 auto 16px;"></div>
                <div style="color: #888;">Loading collection analytics...</div>
            </div>
        `;
        
        try {
            const analytics = await this.apiClient.getCollectionAnalytics(collectionId);
            this.renderCollectionAnalytics(analytics, detailDiv);
        } catch (error) {
            detailDiv.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <div class="empty-state-text">Failed to load analytics</div>
                    <div style="font-size: 12px; margin-top: 8px; color: #888;">${error.message}</div>
                </div>
            `;
        }
    }

    renderCollectionAnalytics(analytics, container) {
        const sentimentEmoji = analytics.overall_sentiment === 'positive' ? '😊' : 
                              analytics.overall_sentiment === 'negative' ? '😞' : '😐';
        
        container.innerHTML = `
            <div class="tab-section">
                <div class="tab-section-title" style="margin-bottom: 0;">📚 ${analytics.collection_name}</div>
                <button class="btn btn--sm btn--gray close-detail-btn" 
                    style="position: absolute; top: 12px; right: 12px; padding: 4px 8px;">✕</button>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-top: 16px;">
                    <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 24px; color: #6366f1; font-weight: 700;">${analytics.conversation_count}</div>
                        <div style="font-size: 11px; color: #888;">Conversations</div>
                    </div>
                    <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 24px; color: #00d4ff; font-weight: 700;">${analytics.total_messages}</div>
                        <div style="font-size: 11px; color: #888;">Messages</div>
                    </div>
                    <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 24px;">${sentimentEmoji}</div>
                        <div style="font-size: 11px; color: #888;">${analytics.overall_sentiment || 'neutral'}</div>
                    </div>
                </div>
                
                ${analytics.sentiment_distribution ? `
                <div style="margin-top: 16px;">
                    <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 12px;">📊 Sentiment Distribution</div>
                    <div style="display: flex; gap: 16px; font-size: 12px;">
                        <span style="color: #00ff88;">😊 ${analytics.sentiment_distribution.positive}</span>
                        <span style="color: #ffd93d;">😐 ${analytics.sentiment_distribution.neutral}</span>
                        <span style="color: #ff6b6b;">😞 ${analytics.sentiment_distribution.negative}</span>
                    </div>
                </div>
                ` : ''}
                
                ${analytics.top_words?.length > 0 ? `
                <div style="margin-top: 16px;">
                    <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 12px;">🔤 Top Words</div>
                    <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                        ${analytics.top_words.slice(0, 10).map(([word, count]) => `
                            <span style="background: rgba(99, 102, 241, 0.2); color: #a5b4fc; padding: 2px 8px; border-radius: 4px; font-size: 11px;">
                                ${word} (${count})
                            </span>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
        
        container.querySelector('.close-detail-btn')?.addEventListener('click', () => {
            container.style.display = 'none';
        });
    }

    async editCollection(collectionId) {
        // Fetch collection details and show edit form
        try {
            const collection = await this.apiClient.getCollection(collectionId);
            const detailDiv = this.container.querySelector('#collectionDetail');
            detailDiv.style.display = 'block';
            
            // Fetch available conversations not in this collection
            const allConversations = await this.apiClient.listConversations();
            const collectionConvIds = new Set((collection.conversations || []).map(c => c.id));
            const availableConversations = allConversations.filter(c => !collectionConvIds.has(c.id));
            
            detailDiv.innerHTML = `
                <div class="tab-section" style="position: relative;">
                    <div class="tab-section-title">✏️ Edit: ${collection.name}</div>
                    <button class="btn btn--sm btn--gray close-detail-btn" 
                        style="position: absolute; top: 12px; right: 12px; padding: 4px 8px;">✕</button>
                    
                    <input type="text" class="tab-input" id="editCollectionName" value="${collection.name}" placeholder="Collection name...">
                    <input type="text" class="tab-input" id="editCollectionDesc" value="${collection.description || ''}" placeholder="Description (optional)...">
                    
                    <div style="margin: 16px 0;">
                        <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 12px;">Current Conversations (${collection.conversations?.length || 0})</div>
                        <div class="saved-list" style="max-height: 150px;">
                            ${(collection.conversations || []).map(conv => `
                                <div class="saved-item" style="padding: 6px 10px;">
                                    <span style="font-size: 12px;">${conv.title || `Conversation ${conv.id}`}</span>
                                    <button class="btn btn--sm btn--red remove-from-collection" data-conv-id="${conv.id}"
                                        style="padding: 2px 6px; font-size: 10px;">-</button>
                                </div>
                            `).join('') || '<div class="empty-state" style="padding: 10px;"><div class="empty-state-text">No conversations</div></div>'}
                        </div>
                    </div>
                    
                    ${availableConversations.length > 0 ? `
                    <div style="margin: 16px 0;">
                        <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 12px;">Add Conversations</div>
                        <select class="tab-select" id="addConversationSelect">
                            <option value="">Select a conversation...</option>
                            ${availableConversations.map(conv => `
                                <option value="${conv.id}">${conv.title || `Conversation ${conv.id}`}</option>
                            `).join('')}
                        </select>
                        <button class="btn btn--sm btn--green" id="addToCollectionBtn" style="margin-top: 8px;">+ Add</button>
                    </div>
                    ` : ''}
                    
                    <div style="display: flex; gap: 8px; margin-top: 16px;">
                        <button class="btn btn--sm btn--green" id="saveCollectionBtn">Save Changes</button>
                    </div>
                </div>
            `;
            
            // Bind handlers
            detailDiv.querySelector('.close-detail-btn')?.addEventListener('click', () => {
                detailDiv.style.display = 'none';
            });
            
            detailDiv.querySelector('#saveCollectionBtn')?.addEventListener('click', async () => {
                const name = detailDiv.querySelector('#editCollectionName')?.value?.trim();
                const description = detailDiv.querySelector('#editCollectionDesc')?.value?.trim();
                if (!name) {
                    alert('Name is required');
                    return;
                }
                try {
                    await this.apiClient.updateCollection(collectionId, { name, description });
                    this.renderCollectionsTab();
                } catch (error) {
                    alert(`Failed to save: ${error.message}`);
                }
            });
            
            detailDiv.querySelector('#addToCollectionBtn')?.addEventListener('click', async () => {
                const convId = detailDiv.querySelector('#addConversationSelect')?.value;
                if (!convId) return;
                try {
                    await this.apiClient.addToCollection(collectionId, convId);
                    this.editCollection(collectionId); // Refresh
                } catch (error) {
                    alert(`Failed to add: ${error.message}`);
                }
            });
            
            detailDiv.querySelectorAll('.remove-from-collection').forEach(btn => {
                btn.addEventListener('click', async () => {
                    try {
                        await this.apiClient.removeFromCollection(collectionId, btn.dataset.convId);
                        this.editCollection(collectionId); // Refresh
                    } catch (error) {
                        alert(`Failed to remove: ${error.message}`);
                    }
                });
            });
            
        } catch (error) {
            alert(`Failed to load collection: ${error.message}`);
        }
    }

    // ==================== ANALYTICS RENDERING HELPERS ====================
    
    renderOverviewCard(aggregated) {
        const card = document.createElement('div');
        card.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            min-width: 180px;
        `;
        
        const sentimentColor = aggregated.overall_sentiment === 'positive' ? '#00ff88' :
                              aggregated.overall_sentiment === 'negative' ? '#ff6b6b' : '#ffd93d';
        
        card.innerHTML = `
            <div style="color: #00d4ff; font-weight: 600; margin-bottom: 12px; font-size: 13px;">📋 Overview</div>
            <div style="display: grid; gap: 8px; font-size: 12px;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #888;">Messages</span>
                    <span style="color: white; font-weight: 600;">${aggregated.total_messages || 0}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #888;">Words</span>
                    <span style="color: white; font-weight: 600;">${aggregated.total_words || 0}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #888;">Unique Words</span>
                    <span style="color: white; font-weight: 600;">${aggregated.unique_words || 0}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #888;">Speakers</span>
                    <span style="color: white; font-weight: 600;">${aggregated.speaker_count || 0}</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px; margin-top: 4px;">
                    <span style="color: #888;">Sentiment</span>
                    <span style="color: ${sentimentColor}; font-weight: 600; text-transform: capitalize;">${aggregated.overall_sentiment || 'neutral'}</span>
                </div>
            </div>
        `;
        
        return card;
    }

    renderMiniSentimentChart(timeline) {
        const card = document.createElement('div');
        card.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            min-width: 200px;
            flex: 1;
            max-width: 300px;
        `;
        
        // Create mini chart using CSS
        const chartHeight = 60;
        const points = timeline.slice(0, 20);
        const maxVal = Math.max(...points.map(p => Math.abs(p.compound)));
        
        card.innerHTML = `
            <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 13px;">📈 Sentiment Flow</div>
            <div style="height: ${chartHeight}px; display: flex; align-items: center; gap: 2px; padding: 4px 0;">
                ${points.map(p => {
                    const height = Math.max(4, Math.abs(p.compound) / (maxVal || 1) * chartHeight * 0.8);
                    const color = p.compound > 0.05 ? '#00ff88' : p.compound < -0.05 ? '#ff6b6b' : '#ffd93d';
                    return `<div style="width: 8px; height: ${height}px; background: ${color}; border-radius: 2px; opacity: 0.8;"
                        title="${p.speaker}: ${p.compound.toFixed(2)}"></div>`;
                }).join('')}
            </div>
        `;
        
        return card;
    }

    renderWordFrequency(wordFreq) {
        const card = document.createElement('div');
        card.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            min-width: 180px;
        `;
        
        // Handle both array of [word, count] tuples and array of {word, count} objects
        let topWords;
        if (Array.isArray(wordFreq) && wordFreq.length > 0) {
            if (Array.isArray(wordFreq[0])) {
                // Already in [word, count] format
                topWords = wordFreq.slice(0, 8);
            } else if (typeof wordFreq[0] === 'object') {
                // Convert {word, count} objects to [word, count] tuples
                topWords = wordFreq.slice(0, 8).map(item => [item.word, item.count]);
            } else {
                topWords = [];
            }
        } else {
            topWords = [];
        }
        
        const maxCount = topWords[0]?.[1] || 1;
        
        card.innerHTML = `
            <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 13px;">🔤 Top Words</div>
            <div style="display: flex; flex-direction: column; gap: 4px;">
                ${topWords.map(([word, count]) => {
                    const width = (count / maxCount) * 100;
                    return `
                        <div style="display: flex; align-items: center; gap: 8px; font-size: 11px;">
                            <span style="width: 60px; color: #888; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${word}</span>
                            <div style="flex: 1; height: 12px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                                <div style="width: ${width}%; height: 100%; background: linear-gradient(90deg, #6366f1, #a855f7); border-radius: 3px;"></div>
                            </div>
                            <span style="color: #666; min-width: 24px; text-align: right;">${count}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
        
        return card;
    }

    renderPOSDistribution(posData) {
        const card = document.createElement('div');
        card.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            min-width: 180px;
        `;
        
        const posEmoji = {
            noun: '📦',
            verb: '⚡',
            adjective: '✨',
            adverb: '💨',
            pronoun: '👤',
            conjunction: '🔗',
            preposition: '📍'
        };
        
        card.innerHTML = `
            <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 13px;">🏷️ Parts of Speech</div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                ${Object.entries(posData).slice(0, 6).map(([pos, count]) => `
                    <div style="background: rgba(99, 102, 241, 0.2); padding: 4px 8px; border-radius: 4px; font-size: 11px; display: flex; align-items: center; gap: 4px;">
                        <span>${posEmoji[pos] || '📌'}</span>
                        <span style="color: #a5b4fc;">${pos}</span>
                        <span style="color: #666;">${count}</span>
                    </div>
                `).join('')}
            </div>
        `;
        
        return card;
    }

    renderSpeakerAnalytics(speakerData) {
        const wrapper = document.createElement('div');
        wrapper.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
        `;
        
        const speakers = Object.entries(speakerData);
        const colors = ['#00d4ff', '#ff6b9d', '#ffd93d', '#00ff88', '#a855f7', '#f97316'];
        
        wrapper.innerHTML = `
            <div style="color: #00d4ff; font-weight: 600; margin-bottom: 12px; font-size: 13px;">👥 Speaker Stats</div>
            <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                ${speakers.map(([name, data], i) => {
                    const sentimentEmoji = this.getSentimentEmoji(data.sentiment?.overall_sentiment);
                    return `
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; min-width: 140px; border-left: 3px solid ${colors[i % colors.length]};">
                            <div style="font-weight: 600; color: ${colors[i % colors.length]}; font-size: 12px; margin-bottom: 6px;">${name}</div>
                            <div style="display: grid; gap: 4px; font-size: 11px; color: #888;">
                                <div>Messages: <span style="color: white;">${data.message_count}</span></div>
                                <div>Words: <span style="color: white;">${data.total_words}</span></div>
                                <div>Sentiment: <span>${sentimentEmoji}</span></div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
        
        return wrapper;
    }

    getSentimentEmoji(sentiment) {
        switch (sentiment) {
            case 'positive': return '😊';
            case 'negative': return '😞';
            default: return '😐';
        }
    }
}
