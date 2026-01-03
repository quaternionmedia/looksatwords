/**
 * Analysis Reporter Module
 * Generates analysis reports and statistics for the UI
 */

import { formatTime } from './models.js';

/**
 * Generates analysis reports and statistics
 */
export class AnalysisReporter {
    constructor(containerId = 'threadAnalysis') {
        this.containerId = containerId;
    }

    /**
     * Generate comprehensive analysis report
     * @param {Thread[]} threads - Analyzed threads
     * @param {Tangent[]} tangents - Detected tangents
     * @param {Map<string, Speaker>} speakers - Map of speakers
     * @param {number} totalDuration - Total conversation duration
     */
    generateReport(threads, tangents, speakers, totalDuration) {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.warn(`Analysis container '${this.containerId}' not found`);
            return;
        }

        container.innerHTML = '';

        // Add speaker summary
        this.addSpeakerAnalysis(container, speakers);

        // Add thread analysis
        threads.forEach(thread => {
            this.addThreadAnalysis(container, thread, totalDuration);
        });

        // Add tangent summary
        if (tangents.length > 0) {
            this.addTangentAnalysis(container, tangents);
        }
    }

    /**
     * Add speaker analysis card
     * @param {HTMLElement} container - Container element
     * @param {Map<string, Speaker>} speakers - Speaker map
     */
    addSpeakerAnalysis(container, speakers) {
        if (speakers.size === 0) return;

        const card = this.createCard('#ffffff');

        const speakerList = Array.from(speakers.entries())
            .map(([name, speaker]) => {
                const color = speaker.color || '#ffffff';
                return `<span style="color: ${color};">${name}</span>`;
            })
            .join(', ');

        card.innerHTML = `
            <div class="card-title">Conversation Participants</div>
            <div class="card-subtitle">${speakerList}</div>
            <div class="card-details">
                ${speakers.size} participants • Node borders show speaker colors
            </div>
        `;

        container.appendChild(card);
    }

    /**
     * Add thread analysis card
     * @param {HTMLElement} container - Container element
     * @param {Thread} thread - Thread to analyze
     * @param {number} totalDuration - Total duration
     */
    addThreadAnalysis(container, thread, totalDuration) {
        const card = this.createCard(thread.color);

        const evolution = thread.points.map(p => formatTime(p.time)).join(' → ');
        const avgIntensity = thread.points.length > 0
            ? (thread.totalIntensity / thread.points.length).toFixed(2)
            : '0.00';
        
        const duration = thread.points.length > 1
            ? thread.points[thread.points.length - 1].time - thread.points[0].time
            : 0;

        const threadName = thread.name.charAt(0).toUpperCase() + thread.name.slice(1);

        card.innerHTML = `
            <div class="card-title" style="color: ${thread.color};">
                ${threadName} Thread
            </div>
            <div class="card-subtitle">Evolution: ${evolution}</div>
            <div class="card-details">
                ${thread.points.length} mentions • 
                Avg intensity: ${avgIntensity} •
                Duration: ${formatTime(duration)}
            </div>
        `;

        container.appendChild(card);
    }

    /**
     * Add tangent analysis card
     * @param {HTMLElement} container - Container element
     * @param {Tangent[]} tangents - Array of tangents
     */
    addTangentAnalysis(container, tangents) {
        const resolvedCount = tangents.filter(t => t.type === 'resolved').length;
        const unresolvedCount = tangents.filter(t => t.type === 'unresolved').length;
        const orphanedCount = tangents.filter(t => t.type === 'orphaned').length;
        const total = tangents.length;
        const resolutionRate = total > 0 ? Math.round((resolvedCount / total) * 100) : 0;

        const card = this.createCard('#ffffff');

        card.innerHTML = `
            <div class="card-title">Conversation Tangents</div>
            <div class="card-subtitle">
                <div class="text-success">✓ Resolved: ${resolvedCount}</div>
                <div class="text-warning">✗ Unresolved: ${unresolvedCount}</div>
                ${orphanedCount > 0 ? `<div class="text-info">◦ Orphaned: ${orphanedCount}</div>` : ''}
            </div>
            <div class="card-details">
                Resolution Rate: ${resolutionRate}% • 
                Dashed arcs show tangent flow
            </div>
        `;

        container.appendChild(card);
    }

    /**
     * Create a styled analysis card
     * @param {string} borderColor - Left border color
     * @returns {HTMLElement} Card element
     */
    createCard(borderColor) {
        const card = document.createElement('div');
        card.className = 'analysis-card fade-in';
        card.style.borderLeftColor = borderColor;
        return card;
    }

    /**
     * Clear the analysis container
     */
    clear() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.innerHTML = '';
        }
    }
}
