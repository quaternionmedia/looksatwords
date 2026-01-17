/**
 * API Client Module
 * Handles communication with the backend API
 */

import { CONFIG } from './config.js';

/**
 * API client for backend communication
 */
export class ApiClient {
    constructor() {
        this.baseUrl = CONFIG.api.endpoint;
        this.isAvailable = false;
    }

    /**
     * Check if the backend API is available
     * @returns {Promise<boolean>} True if API is reachable
     */
    async checkHealth() {
        try {
            const response = await fetch(`${CONFIG.api.base}/health`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            this.isAvailable = response.ok;
            return this.isAvailable;
        } catch (error) {
            console.warn('Backend API not reachable:', error.message);
            this.isAvailable = false;
            return false;
        }
    }

    /**
     * Analyze a conversation via the backend
     * @param {string} text - Conversation text
     * @param {string} [title] - Optional title
     * @returns {Promise<Object>} Analysis response
     */
    async analyzeConversation(text, title = null) {
        if (!this.isAvailable) {
            await this.checkHealth();
        }

        if (!this.isAvailable) {
            throw new Error('Backend API not available');
        }

        const response = await fetch(`${this.baseUrl}/conversations/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                title: title || `Conversation from ${new Date().toLocaleString()}`
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    }

    /**
     * Get list of stored conversations
     * @param {number} [limit=50] - Maximum number of results
     * @param {number} [offset=0] - Offset for pagination
     * @returns {Promise<Array>} List of conversations
     */
    async listConversations(limit = 50, offset = 0) {
        const response = await fetch(
            `${this.baseUrl}/conversations?limit=${limit}&offset=${offset}`,
            {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to list conversations: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Get a specific conversation by ID
     * @param {number} conversationId - Conversation ID
     * @returns {Promise<Object>} Conversation data
     */
    async getConversation(conversationId) {
        const response = await fetch(
            `${this.baseUrl}/conversations/${conversationId}`,
            {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to get conversation: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Delete a conversation
     * @param {number} conversationId - Conversation ID
     * @returns {Promise<Object>} Deletion confirmation
     */
    async deleteConversation(conversationId) {
        const response = await fetch(
            `${this.baseUrl}/conversations/${conversationId}`,
            {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to delete conversation: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Get analytics for a conversation
     * @param {number} conversationId - Conversation ID
     * @returns {Promise<Object>} Analytics data including sentiment, word frequency, POS distribution
     */
    async getConversationAnalytics(conversationId) {
        const response = await fetch(
            `${this.baseUrl}/conversations/${conversationId}/analytics`,
            {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to get analytics: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Analyze conversation with full analytics included in response
     * @param {string} text - Conversation text
     * @param {string} [title] - Optional title
     * @returns {Promise<Object>} Analysis response with analytics
     */
    async analyzeWithAnalytics(text, title = null) {
        if (!this.isAvailable) {
            await this.checkHealth();
        }

        if (!this.isAvailable) {
            throw new Error('Backend API not available');
        }

        const response = await fetch(`${this.baseUrl}/conversations/analyze-with-analytics`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                title: title || `Conversation from ${new Date().toLocaleString()}`
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    }

    /**
     * Extract topics dynamically from conversation text
     * @param {string} text - Conversation text
     * @returns {Promise<Object>} Extracted topics with keywords and scores
     */
    async extractTopics(text) {
        if (!this.isAvailable) {
            await this.checkHealth();
        }

        if (!this.isAvailable) {
            throw new Error('Backend API not available');
        }

        const response = await fetch(`${this.baseUrl}/extract-topics`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    }

    /**
     * Generate a conversation using LLM
     * @param {Object} options - Generation options
     * @param {string} [options.topic] - Topic for conversation (optional, will be generated)
     * @param {number} [options.numSpeakers=2] - Number of speakers
     * @param {number} [options.numMessages=8] - Number of messages
     * @param {string[]} [options.speakerNames] - Custom speaker names
     * @returns {Promise<Object>} Generated conversation
     */
    async generateConversation(options = {}) {
        if (!this.isAvailable) {
            await this.checkHealth();
        }

        if (!this.isAvailable) {
            throw new Error('Backend API not available');
        }

        const response = await fetch(`${this.baseUrl}/generate-conversation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                topic: options.topic || null,
                num_speakers: options.numSpeakers || 2,
                num_messages: options.numMessages || 8,
                speaker_names: options.speakerNames || null
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.status} - ${errorText}`);
        }

        return await response.json();
    }

    /**
     * Export database as JSON
     * @returns {Promise<Object>} Export data
     */
    async exportDatabase() {
        if (!this.isAvailable) {
            await this.checkHealth();
        }

        if (!this.isAvailable) {
            throw new Error('Backend API not available');
        }

        const response = await fetch(`${this.baseUrl}/database/export`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to export database: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Import database from JSON
     * @param {Object} data - Export data to import
     * @param {string} [mode='merge'] - Import mode: 'merge' or 'replace'
     * @returns {Promise<Object>} Import result
     */
    async importDatabase(data, mode = 'merge') {
        if (!this.isAvailable) {
            await this.checkHealth();
        }

        if (!this.isAvailable) {
            throw new Error('Backend API not available');
        }

        const response = await fetch(`${this.baseUrl}/database/import`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ data, mode })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to import database: ${response.status} - ${errorText}`);
        }

        return await response.json();
    }

    // ============ Collection/Corpus API ============

    /**
     * Create a new collection
     * @param {Object} data - Collection data {name, description, conversation_ids}
     * @returns {Promise<Object>} Created collection
     */
    async createCollection(data) {
        if (!this.isAvailable) {
            await this.checkHealth();
        }

        const response = await fetch(`${this.baseUrl}/collections`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`Failed to create collection: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * List all collections
     * @returns {Promise<Array>} List of collections
     */
    async listCollections() {
        const response = await fetch(`${this.baseUrl}/collections`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Failed to list collections: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Get a specific collection by ID
     * @param {number} collectionId - Collection ID
     * @returns {Promise<Object>} Collection data
     */
    async getCollection(collectionId) {
        const response = await fetch(`${this.baseUrl}/collections/${collectionId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Failed to get collection: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Update a collection
     * @param {number} collectionId - Collection ID
     * @param {Object} data - Update data {name, description, conversation_ids}
     * @returns {Promise<Object>} Updated collection
     */
    async updateCollection(collectionId, data) {
        const response = await fetch(`${this.baseUrl}/collections/${collectionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`Failed to update collection: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Delete a collection
     * @param {number} collectionId - Collection ID
     * @returns {Promise<Object>} Deletion result
     */
    async deleteCollection(collectionId) {
        const response = await fetch(`${this.baseUrl}/collections/${collectionId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Failed to delete collection: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Add a conversation to a collection
     * @param {number} collectionId - Collection ID
     * @param {number} conversationId - Conversation ID
     * @returns {Promise<Object>} Result
     */
    async addToCollection(collectionId, conversationId) {
        const response = await fetch(
            `${this.baseUrl}/collections/${collectionId}/conversations/${conversationId}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to add to collection: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Remove a conversation from a collection
     * @param {number} collectionId - Collection ID
     * @param {number} conversationId - Conversation ID
     * @returns {Promise<Object>} Result
     */
    async removeFromCollection(collectionId, conversationId) {
        const response = await fetch(
            `${this.baseUrl}/collections/${collectionId}/conversations/${conversationId}`,
            {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            }
        );

        if (!response.ok) {
            throw new Error(`Failed to remove from collection: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Get aggregated analytics for a collection
     * @param {number} collectionId - Collection ID
     * @returns {Promise<Object>} Collection analytics
     */
    async getCollectionAnalytics(collectionId) {
        const response = await fetch(`${this.baseUrl}/collections/${collectionId}/analytics`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Failed to get collection analytics: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Compare conversations in a collection
     * @param {number} collectionId - Collection ID
     * @returns {Promise<Object>} Comparison data
     */
    async compareCollection(collectionId) {
        const response = await fetch(`${this.baseUrl}/collections/${collectionId}/compare`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Failed to compare collection: ${response.status}`);
        }

        return await response.json();
    }

    // ============ News Gathering & Generation API ============

    /**
     * Check availability of news-related services
     * @returns {Promise<Object>} Service status
     */
    async getNewsServiceStatus() {
        const response = await fetch(`${this.baseUrl}/news/status`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Failed to get news status: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Gather news articles from GNews API
     * @param {Object} params - Search parameters
     * @param {string} [params.keyword] - Search keyword
     * @param {string} [params.topic] - Topic (WORLD, NATION, BUSINESS, etc.)
     * @param {string} [params.location] - Location filter
     * @param {string} [params.site] - Site filter
     * @param {boolean} [params.top] - Get top news
     * @param {number} [params.max_results] - Max results (default 5)
     * @returns {Promise<Object>} Articles with analytics
     */
    async gatherNews(params) {
        const response = await fetch(`${this.baseUrl}/news/gather`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `Failed to gather news: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Generate synthetic news articles using LLM
     * @param {string} seedWord - Topic/seed word
     * @param {number} [count=3] - Number of articles to generate
     * @returns {Promise<Object>} Generated articles with analytics
     */
    async generateNews(seedWord, count = 3) {
        const response = await fetch(`${this.baseUrl}/news/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seed_word: seedWord, count })
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `Failed to generate news: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Analyze a list of news articles
     * @param {Array} articles - List of articles
     * @returns {Promise<Object>} Analytics results
     */
    async analyzeNews(articles) {
        const response = await fetch(`${this.baseUrl}/news/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(articles)
        });

        if (!response.ok) {
            throw new Error(`Failed to analyze news: ${response.status}`);
        }

        return await response.json();
    }

    // ============ Visualization API ============

    /**
     * Generate a word cloud visualization
     * @param {Array<string>} words - List of words
     * @param {Object} [options] - Options (width, height, background_color)
     * @returns {Promise<Object>} Plot response with base64 image
     */
    async generateWordCloud(words, options = {}) {
        const response = await fetch(`${this.baseUrl}/visualize/word-cloud`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ words, ...options })
        });

        if (!response.ok) {
            throw new Error(`Failed to generate word cloud: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Generate a word frequency chart
     * @param {Array} wordFrequency - List of {word, count}
     * @param {number} [topN=20] - Top N words
     * @param {string} [title] - Chart title
     * @returns {Promise<Object>} Plot response with base64 image
     */
    async generateWordFrequencyChart(wordFrequency, topN = 20, title = 'Word Frequency') {
        const response = await fetch(`${this.baseUrl}/visualize/word-frequency`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word_frequency: wordFrequency, top_n: topN, title })
        });

        if (!response.ok) {
            throw new Error(`Failed to generate word frequency chart: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Generate a sentiment chart
     * @param {Array} sentimentData - List of sentiment data points
     * @param {string} [title] - Chart title
     * @returns {Promise<Object>} Plot response with base64 image
     */
    async generateSentimentChart(sentimentData, title = 'Sentiment Analysis') {
        const response = await fetch(`${this.baseUrl}/visualize/sentiment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sentiment_data: sentimentData, title })
        });

        if (!response.ok) {
            throw new Error(`Failed to generate sentiment chart: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Generate a POS distribution pie chart
     * @param {Object} posDistribution - POS tag counts
     * @param {string} [title] - Chart title
     * @returns {Promise<Object>} Plot response with base64 image
     */
    async generatePOSChart(posDistribution, title = 'Parts of Speech') {
        const response = await fetch(`${this.baseUrl}/visualize/pos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pos_distribution: posDistribution, title })
        });

        if (!response.ok) {
            throw new Error(`Failed to generate POS chart: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Generate a speaker comparison chart
     * @param {Object} speakerAnalytics - Speaker analytics data
     * @param {string} [title] - Chart title
     * @returns {Promise<Object>} Plot response with base64 image
     */
    async generateSpeakerChart(speakerAnalytics, title = 'Speaker Comparison') {
        const response = await fetch(`${this.baseUrl}/visualize/speakers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ speaker_analytics: speakerAnalytics, title })
        });

        if (!response.ok) {
            throw new Error(`Failed to generate speaker chart: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Get all visualizations for a conversation
     * @param {number} conversationId - Conversation ID
     * @returns {Promise<Object>} All visualization plots
     */
    async getConversationVisualizations(conversationId) {
        const response = await fetch(`${this.baseUrl}/conversations/${conversationId}/visualizations`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Failed to get visualizations: ${response.status}`);
        }

        return await response.json();
    }
}

/**
 * UI feedback utilities for API operations
 */
export class UIFeedback {
    /**
     * Show loading indicator (corner indicator for quick operations)
     * @param {boolean} show - Whether to show or hide
     * @param {string} [message='Loading...'] - Loading message
     */
    static showLoading(show, message = 'Loading...') {
        let loader = document.getElementById('loadingIndicator');

        if (show) {
            if (!loader) {
                loader = document.createElement('div');
                loader.id = 'loadingIndicator';
                loader.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: rgba(0, 212, 255, 0.95);
                    color: white;
                    padding: 12px 20px;
                    border-radius: 8px;
                    z-index: 10000;
                    font-weight: bold;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4);
                `;
                document.body.appendChild(loader);
            }
            loader.innerHTML = `
                <div class="loading-spinner-sm"></div>
                <span>${message}</span>
            `;
            loader.style.display = 'flex';
        } else if (loader) {
            loader.remove();
        }
    }

    /**
     * Show full-screen loading overlay for long operations (e.g., before modals load)
     * @param {boolean} show - Whether to show or hide
     * @param {string} [message='Loading...'] - Loading message
     */
    static showModalLoading(show, message = 'Loading...') {
        let overlay = document.getElementById('modalLoadingOverlay');

        if (show) {
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'modalLoadingOverlay';
                overlay.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.85);
                    z-index: 9999;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    gap: 20px;
                    backdrop-filter: blur(4px);
                `;
                document.body.appendChild(overlay);
            }
            overlay.innerHTML = `
                <div class="loading-spinner-lg"></div>
                <div style="
                    color: white;
                    font-size: 18px;
                    font-weight: 600;
                    text-align: center;
                    max-width: 300px;
                ">${message}</div>
                <div style="
                    color: rgba(255,255,255,0.5);
                    font-size: 12px;
                ">Please wait...</div>
            `;
            overlay.style.display = 'flex';
        } else if (overlay) {
            overlay.style.animation = 'fadeOut 0.2s ease-out';
            setTimeout(() => overlay.remove(), 200);
        }
    }

    /**
     * Show a message notification
     * @param {string} text - Message text
     * @param {string} [type='info'] - Message type: 'info', 'success', 'error', 'warning'
     * @param {number} [duration=4000] - Display duration in ms
     */
    static showMessage(text, type = 'info', duration = 4000) {
        const colors = {
            info: '#00d4ff',
            success: '#00ff88',
            error: '#ff6b6b',
            warning: '#ffd93d'
        };

        const messageEl = document.createElement('div');
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type] || colors.info};
            color: ${type === 'warning' ? '#000' : '#fff'};
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10000;
            font-weight: bold;
            animation: slideIn 0.3s ease-out;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        `;
        messageEl.textContent = text;
        document.body.appendChild(messageEl);

        setTimeout(() => {
            messageEl.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => messageEl.remove(), 300);
        }, duration);
    }
}
