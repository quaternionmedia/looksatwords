/**
 * Tangent Detector Module
 * Detects conversation tangents (digressions) and tracks their resolution
 */

import { CONFIG } from './config.js';
import { Tangent } from './models.js';

/**
 * Detects and analyzes conversation tangents
 */
export class TangentDetector {
    constructor(timePoints, threads) {
        this.timePoints = timePoints;
        this.threads = threads;
        this.tangents = [];
    }

    /**
     * Detect all tangents in the conversation
     * @returns {Tangent[]} Detected tangents
     */
    detect() {
        this.tangents = [];

        this.timePoints.forEach((point, index) => {
            if (this.isTangentTrigger(point, index)) {
                const tangent = this.analyzeTangent(point, index);
                if (tangent) {
                    this.tangents.push(tangent);
                }
            }
        });

        // If no tangents found via triggers, try detecting topic shifts
        if (this.tangents.length === 0) {
            this.detectTopicShifts();
        }

        return this.tangents;
    }

    /**
     * Check if a point triggers a tangent
     * @param {TimePoint} point - Time point to check
     * @param {number} index - Index in timePoints array
     * @returns {boolean} True if this triggers a tangent
     */
    isTangentTrigger(point, index) {
        const hasTriggerWord = CONFIG.keywords.tangentTriggers.some(trigger =>
            point.text.toLowerCase().includes(trigger.toLowerCase())
        );

        const hasTopicShift = this.isTopicShift(point, index);

        return hasTriggerWord || hasTopicShift;
    }

    /**
     * Check if there's a topic shift at this point
     * @param {TimePoint} point - Current point
     * @param {number} index - Index in array
     * @returns {boolean} True if there's a topic shift
     */
    isTopicShift(point, index) {
        if (index === 0) return false;

        const currentTopics = this.getPointTopics(point);
        const previousTopics = this.getPointTopics(this.timePoints[index - 1]);

        // Topic shift if no overlap between current and previous topics
        const overlap = currentTopics.filter(topic => previousTopics.includes(topic));
        return currentTopics.length > 0 && previousTopics.length > 0 && overlap.length === 0;
    }

    /**
     * Get topics for a given point
     * @param {TimePoint} point - Point to analyze
     * @returns {string[]} Array of topic names
     */
    getPointTopics(point) {
        const topics = [];
        for (const [topicName, keywords] of Object.entries(CONFIG.keywords.topics)) {
            if (keywords.some(keyword => point.text.includes(keyword))) {
                topics.push(topicName);
            }
        }
        return topics;
    }

    /**
     * Analyze a potential tangent starting at a given point
     * @param {TimePoint} startPoint - Starting point
     * @param {number} startIndex - Index in timePoints
     * @returns {Tangent|null} Analyzed tangent or null
     */
    analyzeTangent(startPoint, startIndex) {
        let tangentTopics = this.getPointTopics(startPoint);

        // Fallback topic detection for off-topic content
        if (tangentTopics.length === 0) {
            const personalKeywords = ['game', 'sport', 'weather', 'food', 'movie', 'music', 'player', 'team'];
            const hasPersonalTrigger = personalKeywords.some(word =>
                startPoint.text.toLowerCase().includes(word)
            );
            tangentTopics = hasPersonalTrigger ? ['personal'] : ['general'];
        }

        // Find tangent resolution
        let endIndex = startIndex;
        let resolved = false;
        let resolutionPoint = null;

        for (let i = startIndex + 1; i < this.timePoints.length; i++) {
            const point = this.timePoints[i];

            // Check for resolution triggers
            const hasResolutionTrigger = CONFIG.keywords.resolutionTriggers.some(keyword =>
                point.text.toLowerCase().includes(keyword.toLowerCase())
            );

            if (hasResolutionTrigger || this.returnsToMainThread(point, startIndex)) {
                resolved = true;
                resolutionPoint = point;
                endIndex = i;
                break;
            }

            // Limit tangent span to 3 points without continuation
            if (i - startIndex > 2 && !this.isTangentContinuing(point, tangentTopics)) {
                endIndex = i - 1;
                break;
            }
        }

        // Determine tangent type
        let type = 'unresolved';
        if (resolved) {
            type = 'resolved';
        } else if (endIndex === startIndex || endIndex === startIndex + 1) {
            type = 'orphaned';
        }

        return new Tangent({
            startTime: startPoint.time,
            endTime: this.timePoints[endIndex]?.time || startPoint.time + 30,
            startIndex: startIndex,
            endIndex: endIndex,
            type: type,
            topics: tangentTopics,
            startText: startPoint.originalLine,
            resolutionText: resolutionPoint?.originalLine || null,
            sourceThread: this.findSourceThread(startPoint, startIndex),
            targetThread: resolved ? this.findTargetThread(resolutionPoint, endIndex) : null
        });
    }

    /**
     * Check if point returns to main thread
     * @param {TimePoint} point - Point to check
     * @param {number} tangentStartIndex - Index where tangent started
     * @returns {boolean} True if returns to main thread
     */
    returnsToMainThread(point, tangentStartIndex) {
        if (tangentStartIndex === 0) return false;

        const preTangentTopics = this.getPointTopics(this.timePoints[tangentStartIndex - 1]);
        const currentTopics = this.getPointTopics(point);

        return preTangentTopics.some(topic => currentTopics.includes(topic));
    }

    /**
     * Check if tangent is continuing
     * @param {TimePoint} point - Current point
     * @param {string[]} tangentTopics - Topics in the tangent
     * @returns {boolean} True if tangent is continuing
     */
    isTangentContinuing(point, tangentTopics) {
        const currentTopics = this.getPointTopics(point);
        return tangentTopics.some(topic => currentTopics.includes(topic));
    }

    /**
     * Find the source thread for a tangent
     * @param {TimePoint} point - Starting point
     * @param {number} index - Index in timePoints
     * @returns {Thread|null} Source thread or null
     */
    findSourceThread(point, index) {
        const activeThreads = this.threads.filter(thread =>
            thread.points.some(p => Math.abs(p.time - point.time) <= 30)
        );
        return activeThreads.length > 0 ? activeThreads[0] : this.threads[0] || null;
    }

    /**
     * Find the target thread after resolution
     * @param {TimePoint|null} resolutionPoint - Resolution point
     * @param {number} endIndex - End index
     * @returns {Thread|null} Target thread or null
     */
    findTargetThread(resolutionPoint, endIndex) {
        if (!resolutionPoint) return null;

        const postResolutionThreads = this.threads.filter(thread =>
            thread.points.some(p => Math.abs(p.time - resolutionPoint.time) <= 30)
        );
        return postResolutionThreads.length > 0 ? postResolutionThreads[0] : null;
    }

    /**
     * Detect tangents from topic shifts when no trigger words found
     */
    detectTopicShifts() {
        for (let i = 1; i < this.timePoints.length - 1; i++) {
            const prevTopics = this.getPointTopics(this.timePoints[i - 1]);
            const currTopics = this.getPointTopics(this.timePoints[i]);
            const nextTopics = this.getPointTopics(this.timePoints[i + 1]);

            // Detect orphaned topic that doesn't continue
            if (currTopics.length > 0 &&
                !currTopics.some(topic => prevTopics.includes(topic)) &&
                currTopics.some(topic => nextTopics.includes(topic))) {

                const tangent = new Tangent({
                    startTime: this.timePoints[i].time,
                    endTime: this.timePoints[i + 1].time,
                    startIndex: i,
                    endIndex: i + 1,
                    type: 'orphaned',
                    topics: currTopics,
                    startText: this.timePoints[i].originalLine,
                    resolutionText: null,
                    sourceThread: this.findSourceThread(this.timePoints[i], i),
                    targetThread: null
                });

                this.tangents.push(tangent);
            }
        }
    }

    /**
     * Get all detected tangents
     * @returns {Tangent[]} Array of tangents
     */
    getTangents() {
        return this.tangents;
    }
}
