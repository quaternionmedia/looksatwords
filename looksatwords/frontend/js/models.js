/**
 * Data Models for Conversation Thread Visualizer
 * Clean class definitions for domain objects
 */

import { CONFIG } from './config.js';

/**
 * Represents a speaker in the conversation
 */
export class Speaker {
    constructor(name, index = 0) {
        this.name = name;
        this.color = CONFIG.colors.speakers[index % CONFIG.colors.speakers.length];
        this.index = index;
        this.contributions = 0;
    }

    getInitial() {
        return this.name.charAt(0).toUpperCase();
    }

    toJSON() {
        return {
            name: this.name,
            color: this.color,
            contributions: this.contributions
        };
    }
}

/**
 * Represents a single point in time in the conversation
 */
export class TimePoint {
    constructor(data) {
        this.time = data.time;
        this.text = data.text;
        this.originalLine = data.originalLine;
        this.speaker = data.speaker;
        this.speakerInfo = data.speakerInfo;
        this.index = data.index;
    }

    /**
     * Get topics present in this time point
     */
    getTopics() {
        const topics = [];
        for (const [topicName, keywords] of Object.entries(CONFIG.keywords.topics)) {
            if (keywords.some(keyword => this.text.includes(keyword))) {
                topics.push(topicName);
            }
        }
        return topics;
    }

    /**
     * Check if this point contains a tangent trigger
     */
    hasTangentTrigger() {
        return CONFIG.keywords.tangentTriggers.some(trigger =>
            this.text.toLowerCase().includes(trigger.toLowerCase())
        );
    }

    /**
     * Check if this point contains a resolution trigger
     */
    hasResolutionTrigger() {
        return CONFIG.keywords.resolutionTriggers.some(trigger =>
            this.text.toLowerCase().includes(trigger.toLowerCase())
        );
    }
}

/**
 * Represents a conversation thread/topic
 */
export class Thread {
    constructor(name, index = 0) {
        this.name = name;
        this.color = CONFIG.colors.threads[index % CONFIG.colors.threads.length];
        this.points = [];
        this.totalIntensity = 0;
    }

    /**
     * Add a point to this thread
     */
    addPoint(timePoint, intensity) {
        this.points.push({
            time: timePoint.time,
            text: timePoint.originalLine,
            speaker: timePoint.speaker,
            speakerInfo: timePoint.speakerInfo,
            intensity: intensity
        });
        this.totalIntensity += intensity;
    }

    /**
     * Get average intensity of this thread
     */
    getAverageIntensity() {
        return this.points.length > 0 ? this.totalIntensity / this.points.length : 0;
    }

    /**
     * Get the duration of this thread
     */
    getDuration() {
        if (this.points.length < 2) return 0;
        return this.points[this.points.length - 1].time - this.points[0].time;
    }

    /**
     * Get time range formatted as string
     */
    getTimeRange() {
        if (this.points.length === 0) return '';
        return this.points.map(p => formatTime(p.time)).join(' → ');
    }
}

/**
 * Represents a conversation tangent/digression
 */
export class Tangent {
    constructor(data) {
        this.startTime = data.startTime;
        this.endTime = data.endTime;
        this.startIndex = data.startIndex;
        this.endIndex = data.endIndex;
        this.type = data.type; // 'resolved', 'unresolved', 'orphaned'
        this.topics = data.topics || [];
        this.startText = data.startText;
        this.resolutionText = data.resolutionText || null;
        this.sourceThread = data.sourceThread || null;
        this.targetThread = data.targetThread || null;
    }

    /**
     * Get the color for this tangent based on its type
     */
    getColor() {
        return CONFIG.colors.tangents[this.type] || CONFIG.colors.tangents.unresolved;
    }

    /**
     * Get the duration of this tangent
     */
    getDuration() {
        return this.endTime - this.startTime;
    }

    /**
     * Check if this tangent is active at a given time
     */
    isActiveAt(time) {
        return time >= this.startTime && time <= this.endTime;
    }
}

/**
 * Container for all conversation analysis data
 */
export class ConversationData {
    constructor() {
        this.timePoints = [];
        this.threads = [];
        this.tangents = [];
        this.speakers = new Map();
        this.totalDuration = 0;
        this.conversationId = null;
    }

    /**
     * Clear all data
     */
    clear() {
        this.timePoints = [];
        this.threads = [];
        this.tangents = [];
        this.speakers.clear();
        this.totalDuration = 0;
        this.conversationId = null;
    }

    /**
     * Get statistics about the conversation
     */
    getStats() {
        const resolvedTangents = this.tangents.filter(t => t.type === 'resolved').length;
        const totalTangents = this.tangents.length;
        
        return {
            speakerCount: this.speakers.size,
            threadCount: this.threads.length,
            tangentCount: totalTangents,
            resolvedTangents: resolvedTangents,
            unresolvedTangents: totalTangents - resolvedTangents,
            resolutionRate: totalTangents > 0 
                ? Math.round((resolvedTangents / totalTangents) * 100) 
                : 0,
            totalDuration: this.totalDuration,
            timePointCount: this.timePoints.length
        };
    }
}

/**
 * Format seconds to MM:SS string
 */
export function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}
