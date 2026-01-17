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
}

/**
 * UI feedback utilities for API operations
 */
export class UIFeedback {
    /**
     * Show loading indicator
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
                    background: rgba(0, 212, 255, 0.9);
                    color: white;
                    padding: 12px 20px;
                    border-radius: 8px;
                    z-index: 10000;
                    font-weight: bold;
                `;
                document.body.appendChild(loader);
            }
            loader.innerHTML = `⏳ ${message}`;
            loader.style.display = 'block';
        } else if (loader) {
            loader.remove();
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
