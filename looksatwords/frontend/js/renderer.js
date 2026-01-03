/**
 * Visualization Renderer Module
 * Handles all DOM rendering for the conversation visualization
 */

import { CONFIG } from './config.js';
import { formatTime } from './models.js';

/**
 * Handles visual rendering of the conversation visualization
 */
export class VisualizationRenderer {
    constructor(canvasId, svgId = 'svgContainer') {
        this.canvas = document.getElementById(canvasId);
        this.svgId = svgId;
        this.svg = null;
        this.dimensions = null;
        
        if (!this.canvas) {
            throw new Error(`Canvas element with id '${canvasId}' not found`);
        }
    }

    /**
     * Get canvas dimensions
     * @returns {Object} Dimensions object
     */
    getCanvasDimensions() {
        const rect = this.canvas.getBoundingClientRect();
        // Use computed style as fallback for hidden/zero-sized elements
        const computedStyle = window.getComputedStyle(this.canvas);
        let width = rect.width || parseFloat(computedStyle.width) || this.canvas.offsetWidth;
        let height = rect.height || parseFloat(computedStyle.height) || this.canvas.offsetHeight;
        
        // Ensure minimum dimensions to prevent 0,0 clustering
        width = Math.max(width, 800);
        height = Math.max(height, 400);
        
        return {
            width: width,
            height: height,
            padding: CONFIG.dimensions.canvasPadding
        };
    }

    /**
     * Clear the visualization canvas
     */
    clear() {
        this.canvas.innerHTML = `
            <div class="time-indicator" id="timeIndicator"></div>
            <svg class="svg-container" id="${this.svgId}"></svg>
        `;
        this.svg = document.getElementById(this.svgId);
    }

    /**
     * Render the complete visualization
     * @param {Thread[]} threads - Conversation threads
     * @param {Tangent[]} tangents - Detected tangents
     * @param {Map<string, Speaker>} speakers - Speaker map
     * @param {number} totalDuration - Total conversation duration
     */
    render(threads, tangents, speakers, totalDuration) {
        this.clear();
        this.dimensions = this.getCanvasDimensions();

        this.renderTimeline(totalDuration);
        this.renderThreads(threads, totalDuration);
        this.renderTangents(tangents, threads, totalDuration);
        this.renderSpeakerLegend(speakers);
    }

    /**
     * Render the timeline axis
     * @param {number} totalDuration - Total duration in seconds
     */
    renderTimeline(totalDuration) {
        const timeline = document.createElement('div');
        timeline.className = 'timeline-axis';
        this.canvas.appendChild(timeline);

        const markerCount = Math.min(10, Math.ceil(totalDuration / 30));
        
        for (let i = 0; i <= markerCount; i++) {
            const time = (i / markerCount) * totalDuration;
            const position = (i / markerCount) * 100;

            // Create marker
            const marker = document.createElement('div');
            marker.className = 'timeline-marker';
            marker.style.left = `${position}%`;
            timeline.appendChild(marker);

            // Create label
            const label = document.createElement('div');
            label.className = 'timeline-label';
            label.style.left = `${position}%`;
            label.textContent = formatTime(time);
            timeline.appendChild(label);
        }
    }

    /**
     * Render all threads
     * @param {Thread[]} threads - Array of threads
     * @param {number} totalDuration - Total duration
     */
    renderThreads(threads, totalDuration) {
        // Ensure totalDuration is valid to prevent division by zero
        const safeDuration = Math.max(totalDuration, 1);
        
        threads.forEach((thread, index) => {
            this.renderThreadPath(thread, index, safeDuration);
            this.renderThreadNodes(thread, index, safeDuration);
            this.renderThreadLabel(thread, index);
        });
    }

    /**
     * Render a thread path (SVG line)
     * @param {Thread} thread - Thread to render
     * @param {number} threadIndex - Thread index
     * @param {number} totalDuration - Total duration
     */
    renderThreadPath(thread, threadIndex, totalDuration) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const pathData = this.generateThreadPath(thread, threadIndex, totalDuration);

        path.setAttribute('d', pathData);
        path.setAttribute('stroke', thread.color);
        path.setAttribute('stroke-width', '3');
        path.setAttribute('fill', 'none');
        path.setAttribute('opacity', '0');
        path.classList.add('thread-path');
        path.id = `thread-path-${threadIndex}`;

        this.svg.appendChild(path);
    }

    /**
     * Calculate X position for a given time
     * @param {number} time - Time in seconds
     * @param {number} totalDuration - Total duration
     * @returns {number} X coordinate
     */
    calculateX(time, totalDuration) {
        const padding = CONFIG.dimensions.canvasPadding;
        const usableWidth = this.dimensions.width - (2 * padding);
        const safeDuration = Math.max(totalDuration, 1);
        return padding + (time / safeDuration) * usableWidth;
    }

    /**
     * Calculate Y position for a given thread and point
     * @param {number} threadIndex - Thread index
     * @param {number} time - Time value for wave effect
     * @param {number} intensity - Point intensity
     * @returns {number} Y coordinate
     */
    calculateY(threadIndex, time, intensity) {
        const { canvasPadding, threadSpacing } = CONFIG.dimensions;
        const baseY = canvasPadding + threadIndex * threadSpacing;
        const waveOffset = Math.sin(time * 0.1) * 20;
        const intensityOffset = (intensity || 0.5) * 30;
        return baseY + waveOffset + intensityOffset;
    }

    /**
     * Generate SVG path data for a thread
     * @param {Thread} thread - Thread to render
     * @param {number} threadIndex - Thread index
     * @param {number} totalDuration - Total duration
     * @returns {string} SVG path data
     */
    generateThreadPath(thread, threadIndex, totalDuration) {
        if (!thread.points || thread.points.length === 0) return '';
        
        const points = thread.points.map(point => ({
            x: this.calculateX(point.time, totalDuration),
            y: this.calculateY(threadIndex, point.time, point.intensity)
        }));

        if (points.length < 2) {
            // Single point - return a small circle instead
            return `M ${points[0].x - 5} ${points[0].y} a 5 5 0 1 0 10 0 a 5 5 0 1 0 -10 0`;
        }

        let pathData = `M ${points[0].x} ${points[0].y}`;

        for (let i = 1; i < points.length; i++) {
            const prev = points[i - 1];
            const curr = points[i];
            
            // Bezier curve control points
            const cp1x = prev.x + (curr.x - prev.x) * 0.3;
            const cp1y = prev.y;
            const cp2x = prev.x + (curr.x - prev.x) * 0.7;
            const cp2y = curr.y;

            pathData += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
        }

        return pathData;
    }

    /**
     * Render nodes for a thread
     * @param {Thread} thread - Thread to render
     * @param {number} threadIndex - Thread index
     * @param {number} totalDuration - Total duration
     */
    renderThreadNodes(thread, threadIndex, totalDuration) {
        const { nodeMinSize, nodeMaxSize } = CONFIG.dimensions;

        if (!thread.points) return;

        thread.points.forEach((point, pointIndex) => {
            const x = this.calculateX(point.time, totalDuration);
            const y = this.calculateY(threadIndex, point.time, point.intensity);

            const node = document.createElement('div');
            node.className = 'thread-node';
            node.id = `thread-node-${threadIndex}-${pointIndex}`;

            const size = Math.max(nodeMinSize, nodeMaxSize * point.intensity);
            const speakerColor = point.speakerInfo?.color || '#ffffff';
            const speakerInitial = point.speaker ? point.speaker.charAt(0).toUpperCase() : '';

            node.style.cssText = `
                left: ${x - size / 2}px;
                top: ${y - size / 2}px;
                width: ${size}px;
                height: ${size}px;
                background: radial-gradient(circle, ${thread.color}88, ${thread.color}CC);
                color: white;
                border: 3px solid ${speakerColor};
                font-size: ${Math.max(8, size * 0.3)}px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
                box-shadow: 0 0 8px ${speakerColor};
            `;

            node.textContent = speakerInitial;
            node.title = `${point.speaker}: ${point.text}`;

            this.canvas.appendChild(node);
        });
    }

    /**
     * Render a thread label
     * @param {Thread} thread - Thread to render
     * @param {number} threadIndex - Thread index
     */
    renderThreadLabel(thread, threadIndex) {
        const label = document.createElement('div');
        label.className = 'thread-label';
        label.style.color = thread.color;
        label.style.top = `${CONFIG.dimensions.canvasPadding + threadIndex * CONFIG.dimensions.threadSpacing}px`;
        label.textContent = thread.name.charAt(0).toUpperCase() + thread.name.slice(1);
        this.canvas.appendChild(label);
    }

    /**
     * Render all tangents
     * @param {Tangent[]} tangents - Array of tangents
     * @param {Thread[]} threads - Array of threads
     * @param {number} totalDuration - Total duration
     */
    renderTangents(tangents, threads, totalDuration) {
        if (!tangents || tangents.length === 0) return;
        
        const safeDuration = Math.max(totalDuration, 1);
        
        tangents.forEach((tangent, index) => {
            this.renderTangentArc(tangent, index, threads, safeDuration);
            this.renderTangentMarkers(tangent, index, threads, safeDuration);
        });
    }

    /**
     * Render a tangent arc
     * @param {Tangent} tangent - Tangent to render
     * @param {number} tangentIndex - Tangent index
     * @param {Thread[]} threads - Array of threads
     * @param {number} totalDuration - Total duration
     */
    renderTangentArc(tangent, tangentIndex, threads, totalDuration) {
        const sourceThread = tangent.sourceThread;
        if (!sourceThread || !threads.includes(sourceThread)) return;

        const { canvasPadding, threadSpacing } = CONFIG.dimensions;
        const startX = this.calculateX(tangent.startTime, totalDuration);
        const endX = this.calculateX(tangent.endTime, totalDuration);

        const sourceThreadIndex = threads.indexOf(sourceThread);
        const sourceY = canvasPadding + sourceThreadIndex * threadSpacing + 20;

        // Calculate arc control points
        const controlY = sourceY - 80;
        const endY = sourceY + 40;
        const midX = startX + (endX - startX) * 0.5;

        const pathData = tangent.type === 'resolved'
            ? `M ${startX} ${sourceY} Q ${midX} ${controlY} ${endX} ${sourceY}`
            : `M ${startX} ${sourceY} Q ${midX} ${controlY} ${endX} ${endY}`;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', pathData);
        path.setAttribute('stroke', tangent.getColor());
        path.setAttribute('stroke-width', '3');
        path.setAttribute('stroke-dasharray', '6,6');
        path.setAttribute('fill', 'none');
        path.setAttribute('opacity', '0.7');
        path.classList.add('tangent-arc');
        path.id = `tangent-arc-${tangentIndex}`;

        this.svg.appendChild(path);
    }

    /**
     * Render tangent markers (start/end points)
     * @param {Tangent} tangent - Tangent to render
     * @param {number} tangentIndex - Tangent index
     * @param {Thread[]} threads - Array of threads
     * @param {number} totalDuration - Total duration
     */
    renderTangentMarkers(tangent, tangentIndex, threads, totalDuration) {
        const sourceThread = tangent.sourceThread;
        if (!sourceThread || !threads.includes(sourceThread)) return;

        const { canvasPadding, threadSpacing } = CONFIG.dimensions;
        const startX = this.calculateX(tangent.startTime, totalDuration);
        const endX = this.calculateX(tangent.endTime, totalDuration);

        const sourceThreadIndex = threads.indexOf(sourceThread);
        const sourceY = canvasPadding + sourceThreadIndex * threadSpacing + 20;
        const endY = tangent.type === 'resolved' ? sourceY : sourceY + 40;

        // Start marker
        this.createTangentMarker(tangent, 'start', startX, sourceY, tangentIndex);

        // End marker
        this.createTangentMarker(tangent, 'end', endX, endY, tangentIndex);
    }

    /**
     * Create a single tangent marker
     * @param {Tangent} tangent - Parent tangent
     * @param {string} type - 'start' or 'end'
     * @param {number} x - X position
     * @param {number} y - Y position
     * @param {number} index - Tangent index
     */
    createTangentMarker(tangent, type, x, y, index) {
        const marker = document.createElement('div');
        marker.className = `tangent-marker tangent-${type}`;
        marker.id = `tangent-marker-${index}-${type}`;

        const size = type === 'start' ? 10 : 12;

        marker.style.cssText = `
            position: absolute;
            left: ${x - size / 2}px;
            top: ${y - size / 2}px;
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            opacity: 0.8;
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 90;
        `;

        if (type === 'start') {
            marker.style.background = 'rgba(255, 255, 255, 0.8)';
            marker.style.border = `2px solid ${tangent.sourceThread?.color || CONFIG.colors.ui.primary}`;
            marker.style.boxShadow = `0 0 8px ${tangent.sourceThread?.color || CONFIG.colors.ui.primary}`;
        } else {
            marker.style.background = tangent.getColor();
            marker.style.border = '2px solid rgba(255, 255, 255, 0.8)';
            marker.style.boxShadow = `0 0 10px ${tangent.getColor()}`;
        }

        marker.title = type === 'start'
            ? `Tangent: ${tangent.startText}`
            : `${tangent.type === 'resolved' ? 'Resolved' : 'Unresolved'}: ${tangent.resolutionText || 'No resolution'}`;

        this.canvas.appendChild(marker);
    }

    /**
     * Render speaker legend
     * @param {Map<string, Speaker>} speakers - Map of speakers
     */
    renderSpeakerLegend(speakers) {
        if (speakers.size === 0) return;

        const legend = document.createElement('div');
        legend.className = 'speaker-legend';

        speakers.forEach((speaker, name) => {
            const speakerItem = document.createElement('div');
            speakerItem.className = 'speaker-item';

            const colorDot = document.createElement('div');
            colorDot.className = 'speaker-dot';
            colorDot.style.background = speaker.color;
            colorDot.textContent = speaker.getInitial ? speaker.getInitial() : name.charAt(0).toUpperCase();

            const speakerName = document.createElement('span');
            speakerName.textContent = name;

            speakerItem.appendChild(colorDot);
            speakerItem.appendChild(speakerName);
            legend.appendChild(speakerItem);
        });

        this.canvas.appendChild(legend);
    }
}
