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
        this.viewMode = 'topics'; // 'topics' or 'speakers'
        
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
     * @param {string} viewMode - 'topics' or 'speakers'
     */
    render(threads, tangents, speakers, totalDuration, viewMode = 'topics') {
        this.viewMode = viewMode;
        this.clear();
        this.dimensions = this.getCanvasDimensions();

        this.renderTimeline(totalDuration);
        
        if (viewMode === 'speakers') {
            this.renderBySpeaker(threads, speakers, totalDuration);
            // Skip tangents in speaker view - they're topic-related
        } else {
            this.renderThreads(threads, totalDuration);
            this.renderTangents(tangents, threads, totalDuration);
        }
        
        this.renderLegend(speakers, threads, viewMode);
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

        this.messageSlot = this.smallestGap(threads);
        this.renderLaneRules(threads, safeDuration);

        threads.forEach((thread, index) => {
            this.renderThreadPath(thread, index, safeDuration);
            this.renderThreadNodes(thread, index, safeDuration);
            this.renderThreadLabel(thread, index);
        });
    }

    /**
     * The conversation's beat: the smallest step between two moments.
     *
     * Taken from the data rather than assumed, because a transcript with
     * timestamps and one without are spaced differently, and a rest threshold
     * built on a constant would call every gap a rest in one and none in the
     * other.
     *
     * @param {Thread[]} threads
     * @returns {number} seconds between adjacent messages, or 30 if unknowable
     */
    smallestGap(threads) {
        let smallest = Infinity;
        threads.forEach(thread => {
            const times = (thread.points || []).map(p => p.time).sort((a, b) => a - b);
            for (let i = 1; i < times.length; i++) {
                const gap = times[i] - times[i - 1];
                if (gap > 0 && gap < smallest) smallest = gap;
            }
        });
        return Number.isFinite(smallest) ? smallest : 30;
    }

    /**
     * Draw one faint rule per lane, full width, behind everything.
     *
     * The staff. Without it a topic that is silent for most of the
     * conversation is a couple of marks floating in the dark, and a reader
     * cannot tell whether the row is empty or whether they have lost it.
     *
     * @param {Thread[]} threads
     * @param {number} totalDuration
     */
    renderLaneRules(threads, totalDuration) {
        threads.forEach((thread, index) => {
            const y = this.laneY(index);
            const rule = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            rule.setAttribute('x1', 40);
            rule.setAttribute('x2', '100%');
            rule.setAttribute('y1', y);
            rule.setAttribute('y2', y);
            rule.setAttribute('stroke', thread.color);
            rule.setAttribute('stroke-width', '1');
            // DASHED, BECAUSE THE RULE IS WHERE THE REST IS. Solid, it competed
            // with the thread line; at 0.14 it was invisible on this background
            // and a lane's silent stretch looked like the end of the lane
            // rather than a topic nobody was talking about. Dashes read as
            // "still here, nothing sounding" the way a rest does.
            rule.setAttribute('stroke-dasharray', '2,6');
            rule.setAttribute('opacity', '0.35');
            rule.classList.add('lane-rule');
            this.svg.appendChild(rule);
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
        // No `opacity` attribute: `.thread-path` is revealed through
        // inline style by animation.js, and a presentation attribute here
        // loses to the stylesheet while misdirecting anime.js.
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
     * The centre of one topic's lane. One topic, one height, always.
     *
     * A LANE IS A STAFF LINE AND VERTICAL POSITION MEANS ONE THING: which topic
     * this is. It used to mean three things at once -- the lane, plus
     * `sin(time * 0.1) * 20`, plus the point's intensity again. The wave was
     * decoration and carried nothing; the intensity was already in the size of
     * every node. Between them a topic wandered across 50 pixels, lanes crossed
     * each other, and reading "when was this topic live" meant tracing a line
     * through the ones it had tangled with.
     *
     * Now: time reads left to right, topic reads top to bottom, and how loud a
     * moment was reads as the size of the note sitting on the line.
     *
     * @param {number} threadIndex - Thread index
     * @returns {number} Y coordinate of the lane's centre
     */
    laneY(threadIndex) {
        const { canvasPadding, threadSpacing } = CONFIG.dimensions;
        return canvasPadding + threadIndex * threadSpacing;
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

        const y = this.laneY(threadIndex);
        const pts = thread.points.map(point => ({
            x: this.calculateX(point.time, totalDuration),
            time: point.time,
        }));

        if (pts.length < 2) {
            return `M ${pts[0].x - 5} ${y} a 5 5 0 1 0 10 0 a 5 5 0 1 0 -10 0`;
        }

        // A GAP IN A TOPIC IS A REST, AND A REST IS DRAWN AS SILENCE. Every
        // point of a thread used to be joined to the next one, so a topic
        // dropped for four minutes and picked up again drew an unbroken line
        // straight through the part where nobody mentioned it -- which is the
        // opposite of what the picture is for. `restGap` comes from the
        // conversation's own message spacing rather than a constant, so a
        // dense thread and a sparse one are each judged against their own beat.
        const restGap = (this.messageSlot || 30) * 2.5;

        const runs = [[pts[0]]];
        for (let i = 1; i < pts.length; i++) {
            if (pts[i].time - pts[i - 1].time > restGap) {
                runs.push([pts[i]]);
            } else {
                runs[runs.length - 1].push(pts[i]);
            }
        }

        return runs.map(run => {
            if (run.length === 1) {
                // A single sounding moment with silence on both sides. Give it
                // a short stroke so the lane shows something happened, rather
                // than leaving the node floating over an empty line.
                return `M ${run[0].x - 6} ${y} L ${run[0].x + 6} ${y}`;
            }
            return `M ${run[0].x} ${y} L ${run[run.length - 1].x} ${y}`;
        }).join(' ');
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
            // On the line, always. Intensity is the size of the note below.
            const y = this.laneY(threadIndex);

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
        // Centred on the lane it names. It used to sit at the lane's nominal
        // top while the line wandered below it, so on a busy chart the label
        // and its topic were not obviously the same row.
        label.style.top = `${this.laneY(threadIndex) - 9}px`;
        label.textContent = thread.name.charAt(0).toUpperCase() + thread.name.slice(1);
        this.canvas.appendChild(label);
    }

    /**
     * Render visualization by speaker (speaker/time view)
     * Groups all messages by speaker, Y-axis = speakers, X-axis = time
     * @param {Thread[]} threads - Array of threads
     * @param {Map<string, Speaker>} speakers - Speaker map
     * @param {number} totalDuration - Total duration
     */
    renderBySpeaker(threads, speakers, totalDuration) {
        const safeDuration = Math.max(totalDuration, 1);
        const speakerArray = Array.from(speakers.entries());
        
        // Build a speaker-to-index map for Y positioning
        const speakerIndexMap = new Map();
        speakerArray.forEach(([name], index) => {
            speakerIndexMap.set(name, index);
        });
        
        // Collect ALL points from all threads in chronological order for flow lines
        const allPoints = [];
        threads.forEach((thread, threadIndex) => {
            if (!thread.points) return;
            thread.points.forEach((point, pointIndex) => {
                allPoints.push({
                    ...point,
                    threadColor: thread.color,
                    threadName: thread.name,
                    threadIndex,
                    pointIndex,
                    speakerIndex: speakerIndexMap.get(point.speaker) ?? 0
                });
            });
        });
        
        // Sort all points by time for flow visualization
        allPoints.sort((a, b) => a.time - b.time);
        
        // Render speaker labels and baselines
        speakerArray.forEach(([speakerName, speaker], speakerIndex) => {
            this.renderSpeakerLabel(speakerName, speaker, speakerIndex);
        });
        
        // Render conversation flow paths (connecting all points chronologically)
        this.renderConversationFlow(allPoints, speakerArray, safeDuration);
        
        // Render thread-grouped paths (connecting points within same thread)
        threads.forEach((thread, threadIndex) => {
            this.renderSpeakerThreadPath(thread, threadIndex, speakerIndexMap, safeDuration);
        });
        
        // Render all nodes
        allPoints.forEach((point, globalIndex) => {
            this.renderSpeakerNode(point, point.speakerIndex, globalIndex, speakerArray, safeDuration);
        });
    }

    /**
     * Render a speaker label
     */
    renderSpeakerLabel(speakerName, speaker, speakerIndex) {
        const { canvasPadding, threadSpacing } = CONFIG.dimensions;
        const baseY = canvasPadding + speakerIndex * threadSpacing;
        
        const label = document.createElement('div');
        label.className = 'thread-label';
        label.style.color = speaker.color;
        label.style.top = `${baseY}px`;
        label.textContent = speakerName;
        this.canvas.appendChild(label);
    }

    /**
     * Render conversation flow lines connecting all messages chronologically
     */
    renderConversationFlow(allPoints, speakerArray, totalDuration) {
        if (allPoints.length < 2) return;
        
        const { canvasPadding, threadSpacing } = CONFIG.dimensions;
        
        // Create flow path connecting all points in time order
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        
        let pathData = '';
        for (let i = 0; i < allPoints.length; i++) {
            const point = allPoints[i];
            const x = this.calculateX(point.time, totalDuration);
            const baseY = canvasPadding + point.speakerIndex * threadSpacing;
            // Flat, for the same reason the topic lanes are. See laneY().
            const y = baseY + 30;
            
            if (i === 0) {
                pathData = `M ${x} ${y}`;
            } else {
                const prev = allPoints[i - 1];
                const prevX = this.calculateX(prev.time, totalDuration);
                const prevBaseY = canvasPadding + prev.speakerIndex * threadSpacing;
                // Flat, matching the lane it leaves. See laneY().
                const prevY = prevBaseY + 30;
                
                // Use bezier curve for smooth transitions
                const midX = (prevX + x) / 2;
                pathData += ` C ${midX} ${prevY}, ${midX} ${y}, ${x} ${y}`;
            }
        }
        
        path.setAttribute('d', pathData);
        path.setAttribute('stroke', 'rgba(255, 255, 255, 0.2)');
        path.setAttribute('stroke-width', '1');
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-dasharray', '4,4');
        path.classList.add('conversation-flow');
        
        this.svg.appendChild(path);
    }

    /**
     * Render a thread path in speaker view (connects same-thread points)
     */
    renderSpeakerThreadPath(thread, threadIndex, speakerIndexMap, totalDuration) {
        if (!thread.points || thread.points.length < 2) return;
        
        const { canvasPadding, threadSpacing } = CONFIG.dimensions;
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        
        let pathData = '';
        thread.points.forEach((point, i) => {
            const speakerIndex = speakerIndexMap.get(point.speaker) ?? 0;
            const x = this.calculateX(point.time, totalDuration);
            const baseY = canvasPadding + speakerIndex * threadSpacing;
            // Flat, for the same reason the topic lanes are. See laneY().
            const y = baseY + 30;
            
            if (i === 0) {
                pathData = `M ${x} ${y}`;
            } else {
                const prev = thread.points[i - 1];
                const prevSpeakerIndex = speakerIndexMap.get(prev.speaker) ?? 0;
                const prevX = this.calculateX(prev.time, totalDuration);
                const prevBaseY = canvasPadding + prevSpeakerIndex * threadSpacing;
                // Flat, matching the lane it leaves. See laneY().
                const prevY = prevBaseY + 30;
                
                const midX = (prevX + x) / 2;
                pathData += ` C ${midX} ${prevY}, ${midX} ${y}, ${x} ${y}`;
            }
        });
        
        path.setAttribute('d', pathData);
        path.setAttribute('stroke', thread.color);
        path.setAttribute('stroke-width', '2');
        path.setAttribute('fill', 'none');
        // Revealed through inline style; see the note above.
        path.classList.add('thread-path');
        path.id = `speaker-thread-path-${threadIndex}`;
        
        this.svg.appendChild(path);
    }

    /**
     * Render a single node in speaker view
     */
    renderSpeakerNode(point, speakerIndex, globalIndex, speakerArray, totalDuration) {
        const { canvasPadding, threadSpacing, nodeMinSize, nodeMaxSize } = CONFIG.dimensions;
        const [, speaker] = speakerArray[speakerIndex] || ['Unknown', { color: '#ffffff' }];
        
        const x = this.calculateX(point.time, totalDuration);
        const baseY = canvasPadding + speakerIndex * threadSpacing;
        // Flat, for the same reason the topic lanes are. See laneY().
        const y = baseY + 30;
        
        const node = document.createElement('div');
        node.className = 'thread-node';
        node.id = `speaker-node-${speakerIndex}-${globalIndex}`;
        
        const size = Math.max(nodeMinSize, nodeMaxSize * (point.intensity || 0.5));
        
        // Use thread color for fill, speaker color for border
        node.style.cssText = `
            left: ${x - size / 2}px;
            top: ${y - size / 2}px;
            width: ${size}px;
            height: ${size}px;
            background: radial-gradient(circle, ${point.threadColor}88, ${point.threadColor}CC);
            color: white;
            border: 3px solid ${speaker.color};
            font-size: ${Math.max(8, size * 0.25)}px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
            box-shadow: 0 0 8px ${point.threadColor};
            opacity: 1;
            z-index: 50;
        `;
        
        // Show topic initial
        const topicInitial = point.threadName ? point.threadName.charAt(0).toUpperCase() : '?';
        node.textContent = topicInitial;
        node.title = `[${point.threadName}] ${point.speaker}: ${point.text}`;
        
        this.canvas.appendChild(node);
    }

    /**
     * Render a single speaker's lane with their messages
     * @param {string} speakerName - Speaker name
     * @param {Speaker} speaker - Speaker object
     * @param {number} speakerIndex - Index for Y position
     * @param {Array} points - Array of message points for this speaker
     * @param {number} totalDuration - Total duration
     */
    renderSpeakerLane(speakerName, speaker, speakerIndex, points, totalDuration) {
        const { canvasPadding, threadSpacing, nodeMinSize, nodeMaxSize } = CONFIG.dimensions;
        const baseY = canvasPadding + speakerIndex * threadSpacing;
        
        // Render speaker label
        const label = document.createElement('div');
        label.className = 'thread-label';
        label.style.color = speaker.color;
        label.style.top = `${baseY}px`;
        label.textContent = speakerName;
        this.canvas.appendChild(label);
        
        // Render a baseline for the speaker
        if (points.length > 1) {
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            const startX = this.calculateX(points[0].time, totalDuration);
            const endX = this.calculateX(points[points.length - 1].time, totalDuration);
            
            path.setAttribute('d', `M ${startX} ${baseY + 30} L ${endX} ${baseY + 30}`);
            path.setAttribute('stroke', speaker.color);
            path.setAttribute('stroke-width', '2');
            path.setAttribute('fill', 'none');
            path.setAttribute('opacity', '0.5');
            path.classList.add('speaker-lane');
            
            this.svg.appendChild(path);
        } else if (points.length === 1) {
            // Single point - still render baseline as a dot position indicator
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            const x = this.calculateX(points[0].time, totalDuration);
            path.setAttribute('cx', x);
            path.setAttribute('cy', baseY + 30);
            path.setAttribute('r', '3');
            path.setAttribute('fill', speaker.color);
            path.setAttribute('opacity', '0.5');
            this.svg.appendChild(path);
        }
        
        // Render nodes for each message
        points.forEach((point, pointIndex) => {
            const x = this.calculateX(point.time, totalDuration);
            // Flat, for the same reason the topic lanes are. See laneY().
            const y = baseY + 30;
            
            const node = document.createElement('div');
            node.className = 'thread-node';
            node.id = `speaker-node-${speakerIndex}-${pointIndex}`;
            
            const size = Math.max(nodeMinSize, nodeMaxSize * (point.intensity || 0.5));
            
            // Use thread color for the node fill, speaker color for border
            // Include opacity: 1 to override CSS default of opacity: 0
            node.style.cssText = `
                left: ${x - size / 2}px;
                top: ${y - size / 2}px;
                width: ${size}px;
                height: ${size}px;
                background: radial-gradient(circle, ${point.threadColor}88, ${point.threadColor}CC);
                color: white;
                border: 3px solid ${speaker.color};
                font-size: ${Math.max(8, size * 0.25)}px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
                box-shadow: 0 0 8px ${point.threadColor};
                opacity: 1;
                z-index: 50;
            `;
            
            // Show topic initial in speaker view
            const topicInitial = point.threadName ? point.threadName.charAt(0).toUpperCase() : '?';
            node.textContent = topicInitial;
            node.title = `[${point.threadName}] ${point.speaker}: ${point.text}`;
            
            this.canvas.appendChild(node);
        });
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

        const startX = this.calculateX(tangent.startTime, totalDuration);
        const endX = this.calculateX(tangent.endTime, totalDuration);

        const sourceThreadIndex = threads.indexOf(sourceThread);
        const sourceY = this.laneY(sourceThreadIndex);

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
        // Revealed through inline style; see the note in animation.js.
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

        const startX = this.calculateX(tangent.startTime, totalDuration);
        const endX = this.calculateX(tangent.endTime, totalDuration);

        const sourceThreadIndex = threads.indexOf(sourceThread);
        const sourceY = this.laneY(sourceThreadIndex);
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
     * Render legend based on view mode
     * In topics view: show speakers (since Y-axis is topics)
     * In speakers view: show topics (since Y-axis is speakers)
     * @param {Map<string, Speaker>} speakers - Map of speakers
     * @param {Thread[]} threads - Array of threads
     * @param {string} viewMode - 'topics' or 'speakers'
     */
    renderLegend(speakers, threads, viewMode) {
        const legend = document.createElement('div');
        legend.className = 'speaker-legend';
        
        if (viewMode === 'speakers') {
            // Show topics legend (Y-axis already shows speakers)
            if (!threads || threads.length === 0) return;
            
            threads.forEach((thread) => {
                const item = document.createElement('div');
                item.className = 'speaker-item';

                const colorDot = document.createElement('div');
                colorDot.className = 'speaker-dot';
                colorDot.style.background = thread.color;
                colorDot.textContent = thread.name.charAt(0).toUpperCase();

                const itemName = document.createElement('span');
                itemName.textContent = thread.name;

                item.appendChild(colorDot);
                item.appendChild(itemName);
                legend.appendChild(item);
            });
        } else {
            // Show speakers legend (Y-axis already shows topics)
            if (speakers.size === 0) return;
            
            speakers.forEach((speaker, name) => {
                const item = document.createElement('div');
                item.className = 'speaker-item';

                const colorDot = document.createElement('div');
                colorDot.className = 'speaker-dot';
                colorDot.style.background = speaker.color;
                colorDot.textContent = speaker.getInitial ? speaker.getInitial() : name.charAt(0).toUpperCase();

                const itemName = document.createElement('span');
                itemName.textContent = name;

                item.appendChild(colorDot);
                item.appendChild(itemName);
                legend.appendChild(item);
            });
        }

        this.canvas.appendChild(legend);
    }

    /**
     * Render speaker legend (legacy - use renderLegend instead)
     * @param {Map<string, Speaker>} speakers - Map of speakers
     */
    renderSpeakerLegend(speakers) {
        this.renderLegend(speakers, [], 'topics');
    }
}
