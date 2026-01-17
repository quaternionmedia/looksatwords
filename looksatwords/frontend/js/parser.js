/**
 * Conversation Parser Module
 * Handles parsing of conversation text into structured data
 */

import { CONFIG } from './config.js';
import { Speaker, TimePoint } from './models.js';

/**
 * Parses conversation text into structured TimePoint objects
 */
export class ConversationParser {
    constructor() {
        this.speakers = new Map();
        this.timePoints = [];
    }

    /**
     * Parse conversation text into structured data
     * @param {string} text - Raw conversation text
     * @returns {TimePoint[]} Parsed time points sorted by time
     */
    parse(text) {
        if (!text || typeof text !== 'string') {
            throw new Error('Invalid input: text must be a non-empty string');
        }

        const lines = text.split('\n').filter(line => line.trim());
        this.speakers.clear();
        this.timePoints = [];

        lines.forEach((line, index) => {
            try {
                const timePoint = this.parseLine(line, index);
                if (timePoint) {
                    this.timePoints.push(timePoint);
                }
            } catch (error) {
                console.warn(`Failed to parse line ${index + 1}: ${error.message}`);
            }
        });

        // Sort by time
        this.timePoints.sort((a, b) => a.time - b.time);

        return this.timePoints;
    }

    /**
     * Parse a single line of conversation
     * @param {string} line - Single line of text
     * @param {number} index - Line index
     * @returns {TimePoint|null} Parsed time point or null
     */
    parseLine(line, index) {
        if (!line.trim()) return null;

        // Extract timestamp - supports [MM:SS] or MM:SS formats
        const timeMatch = line.match(/\[(\d+):(\d+)\]/) || line.match(/^(\d+):(\d+)/);
        let timeInSeconds = index * 30; // Default: 30 second spacing

        if (timeMatch) {
            timeInSeconds = parseInt(timeMatch[1], 10) * 60 + parseInt(timeMatch[2], 10);
        }

        // Clean the line (remove timestamp)
        let cleanText = line.replace(/\[\d+:\d+\]/, '').trim();

        // Extract speaker
        const speakerMatch = cleanText.match(/^([^:]+):\s*(.+)$/);
        let speaker = 'Unknown';
        
        if (speakerMatch) {
            speaker = speakerMatch[1].trim();
            cleanText = speakerMatch[2].trim();
        }

        // Register speaker if new
        if (!this.speakers.has(speaker)) {
            const speakerObj = new Speaker(speaker, this.speakers.size);
            this.speakers.set(speaker, speakerObj);
        }

        const speakerInfo = this.speakers.get(speaker);
        speakerInfo.contributions++;

        return new TimePoint({
            time: timeInSeconds,
            text: cleanText.toLowerCase(),
            originalLine: line,
            speaker: speaker,
            speakerInfo: speakerInfo,
            index: index
        });
    }

    /**
     * Get all registered speakers
     * @returns {Map<string, Speaker>} Map of speaker names to Speaker objects
     */
    getSpeakers() {
        return this.speakers;
    }

    /**
     * Get the total duration of the conversation
     * @returns {number} Total duration in seconds
     */
    getTotalDuration() {
        if (this.timePoints.length === 0) return 0;
        return Math.max(...this.timePoints.map(p => p.time));
    }

    /**
     * Clear parser state
     */
    clear() {
        this.speakers.clear();
        this.timePoints = [];
    }
}
