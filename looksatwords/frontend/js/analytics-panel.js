/**
 * Analytics Panel Module
 * Bottom panel showing sentiment, word frequency, POS distribution, and speaker analytics
 */

import { CONFIG } from './config.js';

/**
 * Analytics panel renderer - slides up from bottom with resizable divider
 */
export class AnalyticsPanel {
    constructor(containerId = 'analyticsPanel') {
        this.containerId = containerId;
        this.panel = null;
        this.resizeBar = null;
        this.container = null;
        this.isVisible = false;
        this.hasData = false;
        this.analyticsData = null;
        
        // Panel height
        this.panelHeight = 320;
        this.minHeight = 150;
        this.maxHeight = window.innerHeight - 200;
        this.isResizing = false;
        
        // Initialize immediately if DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Initialize the bottom panel structure
     */
    init() {
        // Create resize bar (the draggable divider)
        this.resizeBar = document.createElement('div');
        this.resizeBar.className = 'analytics-resize-bar';
        this.resizeBar.style.cssText = `
            position: fixed;
            bottom: ${this.panelHeight}px;
            left: 0;
            right: 0;
            height: 6px;
            background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent);
            cursor: ns-resize;
            z-index: 1001;
            display: none;
            transition: background 0.2s;
        `;
        
        // Resize bar hover indicator
        const resizeIndicator = document.createElement('div');
        resizeIndicator.style.cssText = `
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 60px;
            height: 4px;
            background: rgba(0, 212, 255, 0.5);
            border-radius: 2px;
        `;
        this.resizeBar.appendChild(resizeIndicator);
        
        this.resizeBar.addEventListener('mousedown', (e) => this.startResize(e));
        this.resizeBar.addEventListener('mouseenter', () => {
            this.resizeBar.style.background = 'linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.6), transparent)';
        });
        this.resizeBar.addEventListener('mouseleave', () => {
            if (!this.isResizing) {
                this.resizeBar.style.background = 'linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent)';
            }
        });
        document.body.appendChild(this.resizeBar);
        
        // Create main panel container
        this.panel = document.createElement('div');
        this.panel.className = 'analytics-panel-bottom';
        this.panel.style.cssText = `
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: ${this.panelHeight}px;
            background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
            border-top: 1px solid rgba(0, 212, 255, 0.3);
            z-index: 1000;
            display: none;
            flex-direction: column;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;
        
        // Create header
        const header = document.createElement('div');
        header.className = 'analytics-panel-header';
        header.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 16px;
            background: rgba(0, 0, 0, 0.3);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            flex-shrink: 0;
        `;
        
        // Title
        const titleEl = document.createElement('div');
        titleEl.style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
        `;
        titleEl.innerHTML = `
            <span style="font-size: 16px;">📊</span>
            <span style="color: #00d4ff; font-weight: 600; font-size: 14px;">Conversation Analytics</span>
        `;
        header.appendChild(titleEl);
        
        // Header right side (shortcut hint + close)
        const headerRight = document.createElement('div');
        headerRight.style.cssText = `
            display: flex;
            align-items: center;
            gap: 12px;
        `;
        headerRight.innerHTML = `
            <span style="color: #666; font-size: 11px;">
                Press <kbd style="background: #333; color: #888; padding: 2px 6px; border-radius: 3px; font-family: monospace;">\`</kbd> to toggle
            </span>
        `;
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'analytics-close-btn';
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: #666;
            font-size: 20px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            line-height: 1;
            transition: all 0.2s;
        `;
        closeBtn.addEventListener('click', () => this.togglePanel(false));
        closeBtn.addEventListener('mouseenter', () => {
            closeBtn.style.color = '#fff';
            closeBtn.style.background = 'rgba(255, 255, 255, 0.1)';
        });
        closeBtn.addEventListener('mouseleave', () => {
            closeBtn.style.color = '#666';
            closeBtn.style.background = 'none';
        });
        headerRight.appendChild(closeBtn);
        header.appendChild(headerRight);
        
        this.panel.appendChild(header);
        
        // Create content container
        this.container = document.createElement('div');
        this.container.id = this.containerId;
        this.container.style.cssText = `
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 16px;
        `;
        this.panel.appendChild(this.container);
        
        document.body.appendChild(this.panel);
        
        // Global mouse events for resize
        document.addEventListener('mousemove', (e) => this.onMouseMove(e));
        document.addEventListener('mouseup', () => this.onMouseUp());
        
        // Keyboard listener for Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.togglePanel(false);
            }
        });
        
        // Update max height on window resize
        window.addEventListener('resize', () => {
            this.maxHeight = window.innerHeight - 200;
            if (this.panelHeight > this.maxHeight) {
                this.panelHeight = this.maxHeight;
                this.updatePanelHeight();
            }
        });
        
        console.log('Analytics panel initialized (bottom panel)');
    }
    
    /**
     * Start resizing the panel
     */
    startResize(e) {
        e.preventDefault();
        this.isResizing = true;
        this.resizeStartY = e.clientY;
        this.resizeStartHeight = this.panelHeight;
        document.body.style.cursor = 'ns-resize';
        document.body.style.userSelect = 'none';
    }
    
    /**
     * Handle mouse move for resize
     */
    onMouseMove(e) {
        if (!this.isResizing) return;
        
        const deltaY = this.resizeStartY - e.clientY;
        const newHeight = Math.max(this.minHeight, Math.min(this.maxHeight, this.resizeStartHeight + deltaY));
        
        this.panelHeight = newHeight;
        this.updatePanelHeight();
    }
    
    /**
     * Handle mouse up
     */
    onMouseUp() {
        if (this.isResizing) {
            this.isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            this.resizeBar.style.background = 'linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent)';
        }
    }
    
    /**
     * Update panel height
     */
    updatePanelHeight() {
        this.panel.style.height = `${this.panelHeight}px`;
        this.resizeBar.style.bottom = `${this.panelHeight}px`;
    }
    
    /**
     * Render all analytics content
     */
    renderAllContent() {
        if (!this.analyticsData) return;
        
        this.container.innerHTML = '';
        
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

    /**
     * Render analytics data
     * @param {Object} analytics - Analytics data from API
     */
    render(analytics) {
        if (!this.container) {
            console.error('Analytics panel: container not found, cannot render');
            return;
        }

        console.log('Rendering analytics panel with data:', analytics);

        // Store analytics data
        this.analyticsData = analytics;
        this.hasData = true;
        
        // Render all content
        this.renderAllContent();
    }

    /**
     * Render overview statistics card
     */
    renderOverviewCard(aggregated) {
        const card = document.createElement('div');
        card.className = 'analytics-card analytics-overview';
        card.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 212, 255, 0.2);
            border-radius: 8px;
            padding: 12px 16px;
            min-width: 280px;
            flex: 1;
        `;

        const sentimentColor = this.getSentimentColor(aggregated.overall_sentiment);
        const sentimentEmoji = this.getSentimentEmoji(aggregated.overall_sentiment);

        card.innerHTML = `
            <div style="color: #00d4ff; font-weight: 600; margin-bottom: 12px; font-size: 13px;">📈 Overview</div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #fff;">${aggregated.total_messages}</div>
                    <div style="font-size: 11px; color: #888;">Messages</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #fff;">${aggregated.total_words}</div>
                    <div style="font-size: 11px; color: #888;">Words</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #fff;">${aggregated.average_words_per_message.toFixed(1)}</div>
                    <div style="font-size: 11px; color: #888;">Avg/Msg</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: ${sentimentColor};">${sentimentEmoji}</div>
                    <div style="font-size: 11px; color: #888;">${aggregated.overall_sentiment}</div>
                </div>
            </div>
            <div style="font-size: 12px; color: #aaa;">
                Compound: <strong>${aggregated.average_sentiment.compound.toFixed(3)}</strong>
                <span style="margin-left: 10px; color: #4ade80;">+${(aggregated.average_sentiment.pos * 100).toFixed(1)}%</span>
                <span style="margin-left: 6px; color: #888;">${(aggregated.average_sentiment.neu * 100).toFixed(1)}%</span>
                <span style="margin-left: 6px; color: #f87171;">-${(aggregated.average_sentiment.neg * 100).toFixed(1)}%</span>
            </div>
        `;

        return card;
    }

    /**
     * Render mini sentiment chart
     */
    renderMiniSentimentChart(timeline) {
        const card = document.createElement('div');
        card.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 212, 255, 0.2);
            border-radius: 8px;
            padding: 16px;
            flex: 1;
            min-width: 300px;
        `;

        const chartWidth = 350;
        const chartHeight = 80;
        const padding = 25;

        const points = timeline.map((p, i) => {
            const x = padding + (i / (timeline.length - 1 || 1)) * (chartWidth - 2 * padding);
            const y = chartHeight / 2 - (p.compound * (chartHeight / 2 - 5));
            return { x, y, ...p };
        });

        const pathData = points.length > 1 
            ? `M ${points.map(p => `${p.x},${p.y}`).join(' L ')}`
            : '';

        card.innerHTML = `
            <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 13px;">📉 Sentiment Flow</div>
            <svg width="100%" viewBox="0 0 ${chartWidth} ${chartHeight}" style="display: block;">
                <line x1="${padding}" y1="${chartHeight/2}" x2="${chartWidth-padding}" y2="${chartHeight/2}" 
                      stroke="#444" stroke-dasharray="4,4" />
                <path d="${pathData}" fill="none" stroke="#00d4ff" stroke-width="2" />
                ${points.map(p => `
                    <circle cx="${p.x}" cy="${p.y}" r="3" 
                            fill="${this.getSentimentColor(p.compound > 0.05 ? 'positive' : p.compound < -0.05 ? 'negative' : 'neutral')}" />
                `).join('')}
            </svg>
        `;

        return card;
    }

    /**
     * Render sentiment timeline chart using SVG
     */
    renderSentimentChart(timeline) {
        const card = document.createElement('div');
        card.className = 'analytics-card analytics-sentiment-chart';
        card.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 212, 255, 0.2);
            border-radius: 8px;
            padding: 16px;
            min-width: 400px;
            flex: 1;
        `;

        const chartWidth = 400;
        const chartHeight = 120;
        const padding = 30;

        const points = timeline.map((p, i) => {
            const x = padding + (i / (timeline.length - 1 || 1)) * (chartWidth - 2 * padding);
            const y = chartHeight / 2 - (p.compound * (chartHeight / 2 - 10));
            return { x, y, ...p };
        });

        const pathData = points.length > 1 
            ? `M ${points.map(p => `${p.x},${p.y}`).join(' L ')}`
            : '';

        const areaPath = points.length > 1
            ? `M ${points[0].x},${chartHeight/2} L ${points.map(p => `${p.x},${p.y}`).join(' L ')} L ${points[points.length-1].x},${chartHeight/2} Z`
            : '';

        card.innerHTML = `
            <div style="color: #00d4ff; font-weight: 600; margin-bottom: 12px; font-size: 13px;">📉 Sentiment Over Time</div>
            <svg width="100%" viewBox="0 0 ${chartWidth} ${chartHeight}" style="display: block;">
                <line x1="${padding}" y1="${chartHeight/2}" x2="${chartWidth-padding}" y2="${chartHeight/2}" 
                      stroke="#444" stroke-dasharray="4,4" />
                <line x1="${padding}" y1="10" x2="${chartWidth-padding}" y2="10" 
                      stroke="#333" stroke-dasharray="2,4" />
                <line x1="${padding}" y1="${chartHeight-10}" x2="${chartWidth-padding}" y2="${chartHeight-10}" 
                      stroke="#333" stroke-dasharray="2,4" />
                
                <text x="10" y="15" fill="#888" font-size="10">+1</text>
                <text x="10" y="${chartHeight/2 + 4}" fill="#888" font-size="10">0</text>
                <text x="10" y="${chartHeight - 5}" fill="#888" font-size="10">-1</text>
                
                <path d="${areaPath}" fill="url(#sentimentGradient)" opacity="0.3" />
                <path d="${pathData}" fill="none" stroke="${CONFIG.colors.ui.primary}" stroke-width="2" />
                
                ${points.map(p => `
                    <circle cx="${p.x}" cy="${p.y}" r="4" 
                            fill="${this.getSentimentColor(p.compound > 0.05 ? 'positive' : p.compound < -0.05 ? 'negative' : 'neutral')}" />
                `).join('')}
                
                <defs>
                    <linearGradient id="sentimentGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="${CONFIG.colors.ui.success}" />
                        <stop offset="50%" stop-color="${CONFIG.colors.ui.primary}" />
                        <stop offset="100%" stop-color="${CONFIG.colors.ui.error}" />
                    </linearGradient>
                </defs>
            </svg>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; font-size: 11px;">
                ${timeline.slice(0, 6).map(p => `
                    <span style="color: ${this.getSentimentColor(p.compound > 0.05 ? 'positive' : p.compound < -0.05 ? 'negative' : 'neutral')}">
                        ${p.speaker}: ${p.compound > 0 ? '+' : ''}${p.compound.toFixed(2)}
                    </span>
                `).join('')}
                ${timeline.length > 6 ? `<span style="color: #666;">...+${timeline.length - 6} more</span>` : ''}
            </div>
        `;

        return card;
    }

    /**
     * Render word frequency visualization
     */
    renderWordFrequency(wordFreq) {
        const card = document.createElement('div');
        card.className = 'analytics-card analytics-word-freq';
        card.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 212, 255, 0.2);
            border-radius: 8px;
            padding: 12px 16px;
            min-width: 200px;
        `;

        const maxCount = Math.max(...wordFreq.map(w => w.count));
        const topWords = wordFreq.slice(0, 8);

        card.innerHTML = `
            <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 13px;">🔤 Top Words</div>
            <div style="display: flex; flex-direction: column; gap: 4px;">
                ${topWords.map((w, i) => {
                    const width = (w.count / maxCount) * 100;
                    const color = CONFIG.colors.threads[i % CONFIG.colors.threads.length];
                    return `
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="color: #aaa; font-size: 11px; min-width: 50px;">${w.word}</span>
                            <div style="flex: 1; height: 4px; background: #333; border-radius: 2px; overflow: hidden;">
                                <div style="width: ${width}%; height: 100%; background: ${color};"></div>
                            </div>
                            <span style="color: #666; font-size: 10px;">${w.count}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        return card;
    }

    /**
     * Render POS distribution chart
     */
    renderPOSDistribution(posDistribution) {
        const card = document.createElement('div');
        card.className = 'analytics-card analytics-pos';
        card.style.cssText = `
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 212, 255, 0.2);
            border-radius: 8px;
            padding: 12px 16px;
            min-width: 180px;
        `;

        const posItems = Object.entries(posDistribution)
            .filter(([_, count]) => count > 0)
            .sort((a, b) => b[1] - a[1]);

        const total = posItems.reduce((sum, [_, count]) => sum + count, 0);

        const posEmoji = {
            noun: '📦',
            verb: '🏃',
            adjective: '🎨',
            adverb: '⚡',
            pronoun: '👤',
            conjunction: '🔗',
            preposition: '📍',
            interjection: '❗'
        };

        card.innerHTML = `
            <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px; font-size: 13px;">📝 Parts of Speech</div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                ${posItems.slice(0, 6).map(([pos, count]) => {
                    const percentage = ((count / total) * 100).toFixed(0);
                    return `
                        <div style="display: flex; align-items: center; gap: 3px; font-size: 11px; background: rgba(255,255,255,0.05); padding: 3px 6px; border-radius: 4px;">
                            <span>${posEmoji[pos] || '📋'}</span>
                            <span style="color: #aaa;">${pos}</span>
                            <span style="color: #666;">${percentage}%</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        return card;
    }

    /**
     * Render speaker analytics section
     */
    renderSpeakerAnalytics(speakerData) {
        const wrapper = document.createElement('div');
        wrapper.style.cssText = `
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            width: 100%;
        `;

        const speakers = Object.entries(speakerData);
        speakers.forEach(([name, data], index) => {
            const color = CONFIG.colors.speakers[index % CONFIG.colors.speakers.length];
            const sentimentColor = this.getSentimentColor(data.sentiment_label);

            const card = document.createElement('div');
            card.className = 'speaker-card';
            card.style.cssText = `
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid ${color}40;
                border-left: 3px solid ${color};
                border-radius: 8px;
                padding: 16px;
                min-width: 200px;
                flex: 1;
            `;

            card.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                    <div style="width: 32px; height: 32px; background: ${color}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; color: #fff;">
                        ${name.charAt(0).toUpperCase()}
                    </div>
                    <div style="color: #fff; font-weight: 600;">${name}</div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; text-align: center; margin-bottom: 8px;">
                    <div>
                        <div style="font-size: 18px; font-weight: 700; color: #fff;">${data.message_count}</div>
                        <div style="font-size: 10px; color: #666;">msgs</div>
                    </div>
                    <div>
                        <div style="font-size: 18px; font-weight: 700; color: #fff;">${data.total_words}</div>
                        <div style="font-size: 10px; color: #666;">words</div>
                    </div>
                    <div>
                        <div style="font-size: 18px; font-weight: 700; color: #fff;">${data.average_words_per_message.toFixed(1)}</div>
                        <div style="font-size: 10px; color: #666;">avg</div>
                    </div>
                </div>
                <div style="text-align: center; color: ${sentimentColor}; font-size: 12px;">
                    ${this.getSentimentEmoji(data.sentiment_label)} ${data.sentiment_label} 
                    (${data.average_sentiment > 0 ? '+' : ''}${data.average_sentiment.toFixed(3)})
                </div>
            `;

            wrapper.appendChild(card);
        });

        return wrapper;
    }

    /**
     * Get color for sentiment
     */
    getSentimentColor(sentiment) {
        if (typeof sentiment === 'number') {
            if (sentiment > 0.05) return CONFIG.colors.ui.success;
            if (sentiment < -0.05) return CONFIG.colors.ui.error;
            return CONFIG.colors.ui.warning;
        }
        switch (sentiment) {
            case 'positive': return CONFIG.colors.ui.success;
            case 'negative': return CONFIG.colors.ui.error;
            default: return CONFIG.colors.ui.warning;
        }
    }

    /**
     * Get emoji for sentiment
     */
    getSentimentEmoji(sentiment) {
        switch (sentiment) {
            case 'positive': return '😊';
            case 'negative': return '😔';
            default: return '😐';
        }
    }

    /**
     * Clear the panel
     */
    clear() {
        if (!this.container) {
            this.init();
        }
        if (this.container) {
            this.container.innerHTML = '';
        }
        this.analyticsData = null;
        this.hasData = false;
    }

    /**
     * Show/hide the panel (called when analytics data is ready)
     */
    toggle(show) {
        this.hasData = show;
        console.log(`Analytics panel data ${show ? 'ready' : 'cleared'}`);
        // Auto-show panel when data becomes available
        if (show && !this.isVisible) {
            this.togglePanel(true);
        }
    }

    /**
     * Toggle the panel visibility
     */
    togglePanel(forceState = null) {
        if (!this.panel) return;
        
        if (!this.hasData && forceState !== false) {
            console.log('No analytics data available yet. Analyze a conversation first.');
            return;
        }
        
        const shouldShow = forceState !== null ? forceState : !this.isVisible;
        this.isVisible = shouldShow;
        
        if (shouldShow) {
            this.panel.style.display = 'flex';
            this.resizeBar.style.display = 'block';
            // Animate slide up
            this.panel.style.transform = 'translateY(100%)';
            this.panel.offsetHeight; // Force reflow
            this.panel.style.transition = 'transform 0.3s ease-out';
            this.panel.style.transform = 'translateY(0)';
        } else {
            this.panel.style.transition = 'transform 0.3s ease-in';
            this.panel.style.transform = 'translateY(100%)';
            setTimeout(() => {
                if (!this.isVisible) {
                    this.panel.style.display = 'none';
                    this.resizeBar.style.display = 'none';
                }
            }, 300);
        }
        
        console.log(`Analytics panel ${shouldShow ? 'opened' : 'closed'}`);
    }

    /**
     * Alias for togglePanel for compatibility
     */
    togglePopup(forceState = null) {
        this.togglePanel(forceState);
    }
}
