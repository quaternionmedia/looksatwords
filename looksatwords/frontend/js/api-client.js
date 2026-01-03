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
