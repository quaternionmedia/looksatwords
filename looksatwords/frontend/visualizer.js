/**
 * ThreadVisualizer - Frontend with backend API integration
 * Analyzes conversation text, identifies topics (threads), detects tangents,
 * and creates animated visualizations of how discussions evolve over time.
 * Now with backend persistence via FastAPI.
 */

// API Configuration
const API_BASE = window.location.origin.includes('localhost') 
    ? 'http://localhost:8000'
    : window.location.origin;
const API_ENDPOINT = `${API_BASE}/api`;

class ThreadVisualizer {
    constructor() {
        this.threads = [];
        this.tangents = [];
        this.timePoints = [];
        this.canvas = document.getElementById('visualization');
        this.svg = document.getElementById('pathContainer');
        this.isPlaying = false;
        this.currentTime = 0;
        this.totalDuration = 0;
        this.playbackSpeed = 1000; // ms per time unit
        this.conversationId = null;  // Track saved conversation
        
        this.threadColors = [
            '#00d4ff', '#ff6b6b', '#00ff88', '#ffd93d', '#ff8cc8',
            '#a8e6cf', '#ffd3a5', '#fd6c9e', '#c1a1d3', '#84fab0'
        ];

        this.speakerColors = [
            '#ff6b6b', '#00d4ff', '#00ff88', '#ffd93d', '#ff8cc8',
            '#a8e6cf', '#ffd3a5', '#fd6c9e', '#c1a1d3', '#84fab0'
        ];
        
        this.speakers = new Map();

        this.topicKeywords = {
            'marketing': ['marketing', 'promotion', 'advertising', 'campaign', 'brand'],
            'technology': ['tech', 'digital', 'software', 'system', 'platform', 'online'],
            'environment': ['environment', 'green', 'sustainable', 'eco', 'climate', 'carbon'],
            'business': ['business', 'strategy', 'revenue', 'profit', 'growth', 'market'],
            'social': ['people', 'team', 'communication', 'relationship', 'community'],
            'finance': ['money', 'budget', 'cost', 'investment', 'financial', 'price'],
            'innovation': ['innovation', 'creative', 'new', 'idea', 'solution', 'future'],
            'quality': ['quality', 'excellence', 'standard', 'improvement', 'better']
        };

        this.tangentTriggers = [
            'but', 'however', 'wait', 'actually', 'speaking of', 'by the way',
            'side note', 'tangent', 'different subject', 'changing topics'
        ];

        this.resolutionKeywords = [
            'back to', 'returning to', 'anyway', 'so back to', 'as we were saying',
            'getting back', 'to return', 'where were we'
        ];
    }

    /**
     * Send conversation to backend for analysis
     */
    async analyzeWithBackend(text, title) {
        try {
            showLoadingIndicator(true);
            const response = await fetch(`${API_ENDPOINT}/conversations/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    title: title || `Conversation from ${new Date().toLocaleString()}`
                })
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            
            // Store conversation ID for later reference
            this.conversationId = data.conversation_id;
            
            // Populate visualizer with backend response
            this.populateFromBackend(data);
            
            showLoadingIndicator(false);
            showMessage(`✓ Conversation saved (ID: ${data.conversation_id})`, 'success');
            
            return data;
        } catch (error) {
            showLoadingIndicator(false);
            showMessage(`✗ Error: ${error.message}`, 'error');
            console.error('Backend analysis failed:', error);
            throw error;
        }
    }

    /**
     * Populate visualizer from backend response
     */
    populateFromBackend(response) {
        this.totalDuration = response.total_duration;
        this.speakers.clear();
        this.threads = [];
        this.tangents = [];

        // Populate speakers
        for (const [name, color] of Object.entries(response.speakers)) {
            this.speakers.set(name, {
                color: color,
                index: this.speakers.size
            });
        }

        // Populate threads
        for (const threadData of response.threads) {
            const thread = {
                name: threadData.name,
                color: threadData.color,
                points: threadData.points,
                totalIntensity: threadData.total_intensity
            };
            this.threads.push(thread);
        }

        // Populate tangents
        for (const tangentData of response.tangents) {
            const tangent = {
                startTime: tangentData.start_time,
                endTime: tangentData.end_time,
                type: tangentData.tangent_type,
                topics: tangentData.topics,
                startText: tangentData.start_text,
                resolutionText: tangentData.resolution_text
            };
            this.tangents.push(tangent);
        }
    }

    parseConversation(text) {
        const lines = text.split('\n').filter(line => line.trim());
        const timePoints = [];
        this.speakers.clear();
        
        lines.forEach((line, index) => {
            const timeMatch = line.match(/\[(\d+):(\d+)\]/) || line.match(/(\d+):(\d+)/);
            let timeInSeconds = index * 30;
            
            if (timeMatch) {
                timeInSeconds = parseInt(timeMatch[1]) * 60 + parseInt(timeMatch[2]);
            }
            
            let speaker = 'Unknown';
            let cleanText = line;
            
            cleanText = cleanText.replace(/\[\d+:\d+\]/, '').trim();
            
            const speakerMatch = cleanText.match(/^([^:]+):\s*(.+)$/);
            if (speakerMatch) {
                speaker = speakerMatch[1].trim();
                cleanText = speakerMatch[2].trim();
            }
            
            if (!this.speakers.has(speaker)) {
                const speakerIndex = this.speakers.size;
                this.speakers.set(speaker, {
                    color: this.speakerColors[speakerIndex % this.speakerColors.length],
                    index: speakerIndex
                });
            }
            
            timePoints.push({
                time: timeInSeconds,
                text: cleanText.toLowerCase(),
                originalLine: line,
                speaker: speaker,
                speakerInfo: this.speakers.get(speaker),
                index: index
            });
        });
        
        this.timePoints = timePoints.sort((a, b) => a.time - b.time);
        this.totalDuration = Math.max(...timePoints.map(p => p.time));
        return timePoints;
    }

    identifyThreads() {
        const threads = new Map();
        
        this.timePoints.forEach(point => {
            for (const [threadName, keywords] of Object.entries(this.topicKeywords)) {
                const relevance = keywords.reduce((score, keyword) => {
                    return score + (point.text.includes(keyword) ? 1 : 0);
                }, 0);
                
                if (relevance > 0) {
                    if (!threads.has(threadName)) {
                        threads.set(threadName, {
                            name: threadName,
                            points: [],
                            color: this.threadColors[threads.size % this.threadColors.length],
                            totalIntensity: 0
                        });
                    }
                    
                    const thread = threads.get(threadName);
                    const intensity = Math.min(1, relevance * 0.3 + 0.2);
                    thread.points.push({
                        time: point.time,
                        intensity: intensity,
                        text: point.originalLine,
                        speaker: point.speaker,
                        speakerInfo: point.speakerInfo
                    });
                    thread.totalIntensity += intensity;
                }
            }
        });
        
        this.threads = Array.from(threads.values())
            .filter(thread => thread.points.length >= 2)
            .sort((a, b) => b.totalIntensity - a.totalIntensity)
            .slice(0, 8);
        
        this.detectTangents();
        
        return this.threads;
    }

    detectTangents() {
        this.tangents = [];
        
        this.timePoints.forEach((point, index) => {
            const hasTangentTrigger = this.tangentTriggers.some(trigger => 
                point.text.toLowerCase().includes(trigger.toLowerCase())
            );
            
            if (hasTangentTrigger) {
                const tangent = this.analyzeTangent(point, index);
                if (tangent) {
                    this.tangents.push(tangent);
                }
            }
        });
        
        return this.tangents;
    }

    analyzeTangent(startPoint, startIndex) {
        const tangentTopics = this.getPointTopics(startPoint);
        
        let endIndex = startIndex;
        let resolved = false;
        let resolutionPoint = null;
        
        for (let i = startIndex + 1; i < this.timePoints.length; i++) {
            const point = this.timePoints[i];
            
            const hasResolutionTrigger = this.resolutionKeywords.some(keyword =>
                point.text.toLowerCase().includes(keyword.toLowerCase())
            );
            
            if (hasResolutionTrigger) {
                resolved = true;
                resolutionPoint = point;
                endIndex = i;
                break;
            }
            
            if (i - startIndex > 2) {
                endIndex = i - 1;
                break;
            }
        }
        
        if (endIndex === startIndex) {
            endIndex = Math.min(startIndex + 1, this.timePoints.length - 1);
        }
        
        let type = 'unresolved';
        if (resolved) {
            type = 'resolved';
        } else if (endIndex === startIndex || endIndex === startIndex + 1) {
            type = 'orphaned';
        }
        
        return {
            startTime: startPoint.time,
            endTime: this.timePoints[endIndex]?.time || startPoint.time + 30,
            startIndex: startIndex,
            endIndex: endIndex,
            type: type,
            topics: tangentTopics,
            resolutionPoint: resolutionPoint,
            startText: startPoint.originalLine,
            resolutionText: resolutionPoint?.originalLine || null
        };
    }

    getPointTopics(point) {
        const topics = [];
        for (const [threadName, keywords] of Object.entries(this.topicKeywords)) {
            if (keywords.some(keyword => point.text.includes(keyword))) {
                topics.push(threadName);
            }
        }
        return topics;
    }

    createVisualization() {
        this.canvas.innerHTML = '<div class="current-time-indicator" id="timeIndicator"></div><svg id="pathContainer"></svg>';
        this.svg = document.getElementById('pathContainer');
        
        const rect = this.canvas.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;
        
        this.createTimeline();
        
        this.threads.forEach((thread, threadIndex) => {
            this.createThreadPath(thread, threadIndex, width, height);
            this.createThreadNodes(thread, threadIndex, width, height);
        });
        
        if (this.tangents.length > 0) {
            this.createIntegratedTangents(width, height);
        }
        
        this.updateAnalysis();
    }

    createTimeline() {
        const timeline = document.createElement('div');
        timeline.className = 'timeline-axis';
        this.canvas.appendChild(timeline);
        
        const markerCount = Math.min(10, Math.ceil(this.totalDuration / 30));
        for (let i = 0; i <= markerCount; i++) {
            const time = (i / markerCount) * this.totalDuration;
            const position = (i / markerCount) * 100;
            
            const marker = document.createElement('div');
            marker.className = 'timeline-marker';
            marker.style.left = `${position}%`;
            timeline.appendChild(marker);
            
            const label = document.createElement('div');
            label.className = 'timeline-label';
            label.style.left = `${position}%`;
            label.textContent = this.formatTime(time);
            timeline.appendChild(label);
        }
        
        this.createSpeakerLegend();
    }

    createSpeakerLegend() {
        if (this.speakers.size === 0) return;
        
        const legend = document.createElement('div');
        legend.className = 'speaker-legend';
        
        Array.from(this.speakers.entries()).forEach(([speaker, info]) => {
            const speakerItem = document.createElement('div');
            speakerItem.style.cssText = `
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 12px;
                color: white;
            `;
            
            const colorDot = document.createElement('div');
            colorDot.style.cssText = `
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: ${info.color};
                border: 2px solid white;
            `;
            
            const speakerName = document.createElement('span');
            speakerName.textContent = speaker;
            
            speakerItem.appendChild(colorDot);
            speakerItem.appendChild(speakerName);
            legend.appendChild(speakerItem);
        });
        
        this.canvas.appendChild(legend);
    }

    createThreadPath(thread, threadIndex, width, height) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const pathData = this.generatePathData(thread, width, height - 100, threadIndex);
        
        path.setAttribute('d', pathData);
        path.setAttribute('stroke', thread.color);
        path.setAttribute('stroke-width', '3');
        path.setAttribute('fill', 'none');
        path.setAttribute('opacity', '0');
        path.classList.add('thread-path');
        path.id = `path-${threadIndex}`;
        
        this.svg.appendChild(path);
        
        const label = document.createElement('div');
        label.className = 'thread-label';
        label.style.color = thread.color;
        label.style.top = `${50 + threadIndex * 60}px`;
        label.textContent = thread.name.charAt(0).toUpperCase() + thread.name.slice(1);
        this.canvas.appendChild(label);
    }

    generatePathData(thread, width, height, threadIndex) {
        const baseY = 50 + threadIndex * 60;
        const points = thread.points.map(point => {
            const x = 50 + (point.time / this.totalDuration) * (width - 100);
            const y = baseY + (Math.sin(point.time * 0.1) * 20) + (point.intensity * 30);
            return { x, y, intensity: point.intensity };
        });
        
        if (points.length < 2) return '';
        
        let pathData = `M ${points[0].x} ${points[0].y}`;
        
        for (let i = 1; i < points.length; i++) {
            const prev = points[i - 1];
            const curr = points[i];
            const cp1x = prev.x + (curr.x - prev.x) * 0.3;
            const cp1y = prev.y;
            const cp2x = prev.x + (curr.x - prev.x) * 0.7;
            const cp2y = curr.y;
            
            pathData += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
        }
        
        return pathData;
    }

    createThreadNodes(thread, threadIndex, width, height) {
        thread.points.forEach((point, pointIndex) => {
            const x = 50 + (point.time / this.totalDuration) * (width - 100);
            const y = 50 + threadIndex * 60 + (Math.sin(point.time * 0.1) * 20) + (point.intensity * 30);
            
            const node = document.createElement('div');
            node.className = 'thread-node';
            node.id = `node-${threadIndex}-${pointIndex}`;
            
            const size = Math.max(12, 20 * point.intensity);
            node.style.cssText = `
                left: ${x - size/2}px;
                top: ${y - size/2}px;
                width: ${size}px;
                height: ${size}px;
                background: radial-gradient(circle, ${thread.color}88, ${thread.color}CC);
                color: ${thread.color};
                border-color: ${thread.color};
                opacity: 0;
                transform: scale(0);
            `;
            
            node.title = `${thread.name} at ${this.formatTime(point.time)}: ${point.text}`;
            this.canvas.appendChild(node);
        });
    }

    createIntegratedTangents(width, height) {
        this.tangents.forEach((tangent, index) => {
            const startX = 50 + (tangent.startTime / this.totalDuration) * (width - 100);
            const endX = 50 + (tangent.endTime / this.totalDuration) * (width - 100);
            
            const sourceY = height / 2;
            const controlY = sourceY - 80;
            const endY = sourceY + 40;
            const midX = startX + (endX - startX) * 0.5;
            
            const tangentPath = `M ${startX} ${sourceY} Q ${midX} ${controlY} ${endX} ${endY}`;
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', tangentPath);
            path.setAttribute('stroke', tangent.type === 'resolved' ? '#00ff88' : '#ff6b6b');
            path.setAttribute('stroke-width', '4');
            path.setAttribute('stroke-dasharray', '8,8');
            path.setAttribute('fill', 'none');
            path.setAttribute('opacity', '0');
            path.classList.add('integrated-tangent', `tangent-${tangent.type}`);
            path.id = `integrated-tangent-${index}`;
            
            this.svg.appendChild(path);
            
            this.createTangentMarker(tangent, 'start', startX, sourceY, index);
            this.createTangentMarker(tangent, 'end', endX, endY, index);
        });
    }

    createTangentMarker(tangent, type, x, y, index) {
        const marker = document.createElement('div');
        marker.className = 'tangent-marker';
        marker.id = `tangent-marker-${index}-${type}`;
        
        const size = type === 'start' ? 12 : 14;
        marker.style.cssText = `
            position: absolute;
            left: ${x - size/2}px;
            top: ${y - size/2}px;
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            opacity: 0;
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 100;
        `;
        
        if (type === 'start') {
            marker.style.background = 'rgba(255, 255, 255, 0.8)';
            marker.style.border = '3px solid #00d4ff';
            marker.style.boxShadow = '0 0 12px #00d4ff';
        } else {
            marker.style.background = tangent.type === 'resolved' ? '#00ff88' : '#ff6b6b';
            marker.style.border = '2px solid rgba(255, 255, 255, 0.8)';
            marker.style.boxShadow = tangent.type === 'resolved' ? '0 0 15px #00ff88' : '0 0 15px #ff6b6b';
        }
        
        marker.title = type === 'start' ? 
            `Tangent: ${tangent.startText}` : 
            `${tangent.type === 'resolved' ? 'Resolved' : 'Unresolved'}: ${tangent.resolutionText || 'N/A'}`;
        
        this.canvas.appendChild(marker);
    }

    animateThreadsAppearance() {
        this.threads.forEach((thread, index) => {
            const path = document.getElementById(`path-${index}`);
            if (path) {
                const pathLength = path.getTotalLength();
                path.style.strokeDasharray = pathLength;
                path.style.strokeDashoffset = pathLength;
                
                anime({
                    targets: path,
                    opacity: [0, 0.7],
                    strokeDashoffset: [pathLength, 0],
                    duration: 2000,
                    delay: index * 300,
                    easing: 'easeOutQuart'
                });
            }
        });
        
        this.threads.forEach((thread, threadIndex) => {
            thread.points.forEach((point, pointIndex) => {
                const node = document.getElementById(`node-${threadIndex}-${pointIndex}`);
                if (node) {
                    anime({
                        targets: node,
                        opacity: [0, 1],
                        scale: [0, 1],
                        duration: 600,
                        delay: (point.time / this.totalDuration) * 2000 + threadIndex * 100,
                        easing: 'easeOutBack'
                    });
                }
            });
        });

        // Animate tangents
        if (this.tangents.length > 0) {
            setTimeout(() => this.animateIntegratedTangents(), 1500);
        }
    }

    animateIntegratedTangents() {
        this.tangents.forEach((tangent, index) => {
            const path = document.getElementById(`integrated-tangent-${index}`);
            if (path) {
                const pathLength = path.getTotalLength();
                path.style.strokeDasharray = pathLength;
                path.style.strokeDashoffset = pathLength;
                
                anime({
                    targets: path,
                    opacity: [0, 0.8],
                    strokeDashoffset: [pathLength, 0],
                    duration: 1200,
                    delay: (tangent.startTime / this.totalDuration) * 800 + 500,
                    easing: 'easeOutQuart'
                });
            }
            
            const startMarker = document.getElementById(`tangent-marker-${index}-start`);
            const endMarker = document.getElementById(`tangent-marker-${index}-end`);
            
            if (startMarker) {
                anime({
                    targets: startMarker,
                    opacity: [0, 1],
                    scale: [0, 1],
                    duration: 500,
                    delay: (tangent.startTime / this.totalDuration) * 800 + 700,
                    easing: 'easeOutBack'
                });
            }
            
            if (endMarker) {
                anime({
                    targets: endMarker,
                    opacity: [0, 1],
                    scale: [0, 1],
                    duration: 500,
                    delay: (tangent.endTime / this.totalDuration) * 800 + 1000,
                    easing: 'easeOutBack'
                });
            }
        });
    }

    playThreadEvolution() {
        if (this.isPlaying) return;
        
        this.isPlaying = true;
        this.currentTime = 0;
        
        const timeIndicator = document.getElementById('timeIndicator');
        const progressFill = document.getElementById('progressFill');
        const timeDisplay = document.getElementById('timeDisplay');
        
        timeIndicator.style.opacity = '1';
        
        const animate = () => {
            if (!this.isPlaying) return;
            
            const progress = this.currentTime / this.totalDuration;
            const canvasWidth = this.canvas.getBoundingClientRect().width;
            
            timeIndicator.style.left = `${50 + progress * (canvasWidth - 100)}px`;
            progressFill.style.width = `${progress * 100}%`;
            timeDisplay.textContent = `${this.formatTime(this.currentTime)} / ${this.formatTime(this.totalDuration)}`;
            
            this.currentTime += 0.5;
            
            if (this.currentTime <= this.totalDuration) {
                setTimeout(animate, 100);
            } else {
                this.isPlaying = false;
                timeIndicator.style.opacity = '0';
            }
        };
        
        animate();
    }

    pausePlayback() {
        this.isPlaying = false;
        document.getElementById('timeIndicator').style.opacity = '0';
    }

    updateAnalysis() {
        const analysis = document.getElementById('threadAnalysis');
        analysis.innerHTML = '';
        
        if (this.speakers.size > 0) {
            const speakerCard = document.createElement('div');
            speakerCard.className = 'thread-card';
            speakerCard.style.borderLeftColor = '#ffffff';
            
            const speakerList = Array.from(this.speakers.entries())
                .map(([name, info]) => `<span style="color: ${info.color};">${name}</span>`)
                .join(', ');
            
            speakerCard.innerHTML = `
                <strong>Conversation Participants</strong>
                <div style="margin-top: 8px; font-size: 12px;">
                    ${speakerList}
                </div>
            `;
            analysis.appendChild(speakerCard);
        }
        
        this.threads.forEach(thread => {
            const card = document.createElement('div');
            card.className = 'thread-card';
            card.style.borderLeftColor = thread.color;
            
            const evolution = thread.points.map(p => this.formatTime(p.time)).join(' → ');
            
            card.innerHTML = `
                <strong style="color: ${thread.color};">${thread.name.charAt(0).toUpperCase() + thread.name.slice(1)} Thread</strong>
                <div class="thread-evolution">
                    Evolution: ${evolution}
                </div>
                <div style="font-size: 11px; margin-top: 5px; opacity: 0.7;">
                    ${thread.points.length} mentions
                </div>
            `;
            analysis.appendChild(card);
        });
        
        if (this.tangents.length > 0) {
            const resolvedCount = this.tangents.filter(t => t.type === 'resolved').length;
            const unresolvedCount = this.tangents.filter(t => t.type === 'unresolved').length;
            
            const summaryCard = document.createElement('div');
            summaryCard.className = 'thread-card';
            summaryCard.style.borderLeftColor = '#ffffff';
            summaryCard.innerHTML = `
                <strong>Tangent Summary</strong>
                <div style="margin-top: 8px; font-size: 12px;">
                    <div style="color: #00ff88;">✓ Resolved: ${resolvedCount}</div>
                    <div style="color: #ff6b6b;">✗ Unresolved: ${unresolvedCount}</div>
                </div>
            `;
            analysis.appendChild(summaryCard);
        }
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    reset() {
        this.isPlaying = false;
        this.currentTime = 0;
        this.conversationId = null;
        this.canvas.innerHTML = '<div class="current-time-indicator" id="timeIndicator"></div><svg id="pathContainer"></svg>';
        this.svg = document.getElementById('pathContainer');
        this.threads = [];
        this.timePoints = [];
        document.getElementById('threadAnalysis').innerHTML = '';
        document.getElementById('progressFill').style.width = '0%';
        document.getElementById('timeDisplay').textContent = '0:00 / 0:00';
    }
}

const visualizer = new ThreadVisualizer();

// ============ UI Helper Functions ============

function showLoadingIndicator(show) {
    let loader = document.getElementById('loadingIndicator');
    if (!loader && show) {
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
        `;
        loader.innerHTML = '⏳ Sending to server...';
        document.body.appendChild(loader);
    } else if (loader && !show) {
        loader.remove();
    }
}

function showMessage(text, type = 'info') {
    const messageEl = document.createElement('div');
    messageEl.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#00ff88' : '#00d4ff'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    messageEl.textContent = text;
    document.body.appendChild(messageEl);
    
    setTimeout(() => messageEl.remove(), 4000);
}

// ============ Event Handlers ============

async function analyzeThreads() {
    const text = document.getElementById('textInput').value.trim();
    if (!text) {
        alert('Please enter conversation text first.');
        return;
    }
    
    try {
        visualizer.reset();
        
        // Send to backend for analysis and persistence
        await visualizer.analyzeWithBackend(text);
        visualizer.createVisualization();
        setTimeout(() => visualizer.animateThreadsAppearance(), 100);
    } catch (error) {
        console.error('Analysis failed:', error);
        showMessage('Failed to analyze conversation. Check console for details.', 'error');
    }
}

function playThreadEvolution() {
    if (visualizer.threads.length === 0) {
        alert('Please analyze threads first.');
        return;
    }
    visualizer.playThreadEvolution();
}

function pausePlayback() {
    visualizer.pausePlayback();
}

function resetVisualization() {
    visualizer.reset();
    document.getElementById('textInput').value = '';
}

function seekToPosition(event) {
    if (visualizer.totalDuration === 0) return;
    
    const rect = event.target.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const progress = clickX / rect.width;
    
    visualizer.currentTime = progress * visualizer.totalDuration;
    document.getElementById('progressFill').style.width = `${progress * 100}%`;
    document.getElementById('timeDisplay').textContent = `${visualizer.formatTime(visualizer.currentTime)} / ${visualizer.formatTime(visualizer.totalDuration)}`;
}

function loadSampleConversation() {
    const sampleText = `[0:00] John: Let's discuss our marketing strategy for next quarter.
[0:30] Sarah: I think we should focus more on digital channels and online platforms.
[1:00] John: That's interesting, but what about our environmental impact with digital advertising?
[1:30] Mike: Good point! We could integrate sustainability messaging into our campaigns.
[2:00] Sarah: Green marketing could really differentiate us from competitors in the market.
[2:30] Lisa: I love the innovation here, but we need to consider the budget and financial implications.
[3:00] John: Actually, speaking of budget - did anyone see the game last night?
[3:30] Mike: Oh yeah! That last-minute goal was incredible. I can't believe they pulled it off.
[4:00] Sarah: Wait, let's get back to our marketing discussion. We were talking about sustainable campaigns.
[4:30] Lisa: Right, so for the financial side, we should also focus on quality content that resonates with eco-conscious consumers.
[5:00] John: Perfect! Let's create a comprehensive strategy that balances profit with purpose.
[5:30] Mike: But just quickly - did you guys know that player transferred to a new team?
[6:00] Sarah: Mike, can we please stay focused? We have deadlines to meet.
[6:30] John: Sarah's right. Anyway, back to our strategy - let's schedule follow-up meetings to develop this further.`;

    document.getElementById('textInput').value = sampleText;
}

// Check backend connectivity on load
window.addEventListener('load', async () => {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (!response.ok) throw new Error('Health check failed');
        console.log('✓ Backend API is reachable');
        showMessage('✓ Connected to backend', 'success');
    } catch (error) {
        console.warn('⚠ Backend API not reachable. Running in local mode.', error);
        showMessage('⚠ Backend not reachable. Using local analysis.', 'info');
    }
});
