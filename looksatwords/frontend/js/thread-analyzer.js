/**
 * Thread Analyzer Module
 * Identifies and creates conversation threads based on topic keywords
 */

import { CONFIG } from './config.js';
import { Thread } from './models.js';

/**
 * Analyzes conversation time points to identify topic threads
 */
export class ThreadAnalyzer {
    constructor(timePoints) {
        this.timePoints = timePoints;
        this.threads = [];
    }

    /**
     * Identify and create conversation threads
     * @returns {Thread[]} Identified threads sorted by intensity
     */
    analyze() {
        const threadMap = new Map();

        this.timePoints.forEach(point => {
            const topicData = this.identifyTopics(point.text);

            topicData.forEach(({ name, intensity }) => {
                if (!threadMap.has(name)) {
                    threadMap.set(name, new Thread(name, threadMap.size));
                }

                const thread = threadMap.get(name);
                thread.addPoint(point, intensity);
            });
        });

        // Filter threads with at least 2 points, sort by intensity, limit to top 8
        this.threads = Array.from(threadMap.values())
            .filter(thread => thread.points.length >= 2)
            .sort((a, b) => b.totalIntensity - a.totalIntensity)
            .slice(0, 8);

        return this.threads;
    }

    /**
     * Identify topics in a text string
     * @param {string} text - Text to analyze
     * @returns {Array<{name: string, intensity: number}>} Topic data
     */
    identifyTopics(text) {
        const topics = [];
        const words = text.split(/\s+/).filter(word => word.length > 3);

        for (const [topicName, keywords] of Object.entries(CONFIG.keywords.topics)) {
            const relevance = keywords.reduce((score, keyword) => {
                return score + (text.includes(keyword) ? 1 : 0);
            }, 0);

            // Check for partial word matches
            const hasWordMatch = words.some(word =>
                keywords.some(kw => word.includes(kw) || kw.includes(word))
            );

            if (relevance > 0 || hasWordMatch) {
                topics.push({
                    name: topicName,
                    intensity: Math.min(1, relevance * 0.3 + 0.2)
                });
            }
        }

        return topics;
    }

    /**
     * Get identified threads
     * @returns {Thread[]} Array of threads
     */
    getThreads() {
        return this.threads;
    }

    /**
     * Find thread active at a specific time
     * @param {number} time - Time in seconds
     * @returns {Thread|null} Active thread or null
     */
    getActiveThreadAt(time) {
        for (const thread of this.threads) {
            const hasPoint = thread.points.some(p =>
                Math.abs(p.time - time) <= 30
            );
            if (hasPoint) return thread;
        }
        return null;
    }
}
