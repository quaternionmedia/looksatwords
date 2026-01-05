/**
 * Animation Controller Module
 * Manages animation and playback functionality
 */

import { CONFIG } from './config.js';
import { formatTime } from './models.js';

/**
 * Controls animations and playback for the visualization
 */
export class AnimationController {
    constructor(renderer) {
        this.renderer = renderer;
        this.isPlaying = false;
        this.currentTime = 0;
        this.totalDuration = 0;
        this.threads = [];
        this.tangents = [];
        this.animationFrameId = null;
        this.viewMode = 'topics';
    }

    /**
     * Set the data to animate
     * @param {Thread[]} threads - Threads to animate
     * @param {Tangent[]} tangents - Tangents to animate
     * @param {number} totalDuration - Total duration
     * @param {string} viewMode - 'topics' or 'speakers'
     */
    setData(threads, tangents, totalDuration, viewMode = 'topics') {
        this.threads = threads;
        this.tangents = tangents;
        this.totalDuration = totalDuration;
        this.viewMode = viewMode;
    }

    /**
     * Animate the initial appearance of visualization elements
     */
    animateAppearance() {
        // Only animate thread paths and nodes in topics view
        // Speaker view nodes already have opacity: 1 set inline
        if (this.viewMode !== 'speakers') {
            this.animateThreadPaths();
            this.animateThreadNodes();
        }

        // Animate tangents after a delay (applies to both views)
        if (this.tangents.length > 0) {
            const delay = this.viewMode === 'speakers' ? 100 : 1500;
            setTimeout(() => this.animateTangents(), delay);
        }
    }

    /**
     * Animate thread paths
     */
    animateThreadPaths() {
        this.threads.forEach((thread, index) => {
            const path = document.getElementById(`thread-path-${index}`);
            if (path) {
                const pathLength = path.getTotalLength();
                path.style.strokeDasharray = pathLength;
                path.style.strokeDashoffset = pathLength;

                if (typeof anime !== 'undefined') {
                    anime({
                        targets: path,
                        opacity: [0, 0.7],
                        strokeDashoffset: [pathLength, 0],
                        duration: CONFIG.animation.pathDuration,
                        delay: index * 300,
                        easing: CONFIG.animation.easing
                    });
                } else {
                    // Fallback for when anime.js is not loaded
                    this.fallbackAnimate(path, {
                        opacity: { from: 0, to: 0.7 },
                        strokeDashoffset: { from: pathLength, to: 0 }
                    }, CONFIG.animation.pathDuration, index * 300);
                }
            }
        });
    }

    /**
     * Animate thread nodes
     */
    animateThreadNodes() {
        this.threads.forEach((thread, threadIndex) => {
            thread.points.forEach((point, pointIndex) => {
                const node = document.getElementById(`thread-node-${threadIndex}-${pointIndex}`);
                if (node) {
                    const delay = (point.time / this.totalDuration) * 1000 + threadIndex * 100;

                    if (typeof anime !== 'undefined') {
                        anime({
                            targets: node,
                            opacity: [0, 1],
                            scale: [0, 1],
                            duration: CONFIG.animation.nodeDuration,
                            delay: delay,
                            easing: 'easeOutBack'
                        });
                    } else {
                        this.fallbackAnimate(node, {
                            opacity: { from: 0, to: 1 },
                            transform: { from: 'scale(0)', to: 'scale(1)' }
                        }, CONFIG.animation.nodeDuration, delay);
                    }
                }
            });
        });
    }

    /**
     * Animate tangents
     */
    animateTangents() {
        this.tangents.forEach((tangent, index) => {
            const path = document.getElementById(`tangent-arc-${index}`);
            if (path) {
                const pathLength = path.getTotalLength();
                path.style.strokeDasharray = pathLength;
                path.style.strokeDashoffset = pathLength;

                const delay = (tangent.startTime / this.totalDuration) * 500;

                if (typeof anime !== 'undefined') {
                    anime({
                        targets: path,
                        opacity: [0, 0.7],
                        strokeDashoffset: [pathLength, 0],
                        duration: CONFIG.animation.tangentDuration,
                        delay: delay,
                        easing: CONFIG.animation.easing
                    });
                }
            }

            // Animate markers
            ['start', 'end'].forEach((type, typeIndex) => {
                const marker = document.getElementById(`tangent-marker-${index}-${type}`);
                if (marker) {
                    const markerDelay = (tangent.startTime / this.totalDuration) * 500 + 300 + typeIndex * 300;

                    if (typeof anime !== 'undefined') {
                        anime({
                            targets: marker,
                            opacity: [0, 0.8],
                            scale: [0, 1],
                            duration: 400,
                            delay: markerDelay,
                            easing: 'easeOutBack'
                        });
                    }
                }
            });
        });
    }

    /**
     * Simple fallback animation when anime.js is not available
     */
    fallbackAnimate(element, properties, duration, delay = 0) {
        setTimeout(() => {
            element.style.transition = `all ${duration}ms ease-out`;
            
            Object.entries(properties).forEach(([prop, { to }]) => {
                if (prop === 'opacity' || prop === 'strokeDashoffset') {
                    element.style[prop] = to;
                } else if (prop === 'transform') {
                    element.style.transform = to;
                }
            });
        }, delay);
    }

    /**
     * Start playback animation
     */
    startPlayback() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        this.currentTime = 0;

        const timeIndicator = document.getElementById('timeIndicator');
        const progressFill = document.getElementById('progressFill');
        const timeDisplay = document.getElementById('timeDisplay');

        if (timeIndicator) {
            timeIndicator.style.opacity = '1';
        }

        const animate = () => {
            if (!this.isPlaying) return;

            const progress = this.currentTime / this.totalDuration;
            const canvas = this.renderer.canvas;
            const canvasWidth = canvas.getBoundingClientRect().width;
            const padding = CONFIG.dimensions.canvasPadding;

            // Update UI elements
            if (timeIndicator) {
                timeIndicator.style.left = `${padding + progress * (canvasWidth - 2 * padding)}px`;
            }
            if (progressFill) {
                progressFill.style.width = `${progress * 100}%`;
            }
            if (timeDisplay) {
                timeDisplay.textContent = `${formatTime(this.currentTime)} / ${formatTime(this.totalDuration)}`;
            }

            // Highlight active elements
            this.highlightActiveElements(this.currentTime);

            this.currentTime += 0.5;

            if (this.currentTime <= this.totalDuration) {
                this.animationFrameId = setTimeout(animate, CONFIG.animation.playbackSpeed);
            } else {
                this.stopPlayback();
            }
        };

        animate();
    }

    /**
     * Highlight elements active at current time
     * @param {number} currentTime - Current playback time
     */
    highlightActiveElements(currentTime) {
        // Highlight active thread nodes
        this.threads.forEach((thread, threadIndex) => {
            thread.points.forEach((point, pointIndex) => {
                const node = document.getElementById(`thread-node-${threadIndex}-${pointIndex}`);
                if (node) {
                    const timeDiff = Math.abs(point.time - currentTime);
                    
                    if (timeDiff <= 3) {
                        const intensity = Math.max(0.3, 1 - timeDiff / 3);
                        node.style.filter = `brightness(${1 + intensity})`;
                        node.style.transform = 'scale(1.3)';
                        node.style.boxShadow = `0 0 ${20 * intensity}px ${point.speakerInfo?.color || thread.color}`;
                    } else {
                        node.style.filter = 'brightness(0.5)';
                        node.style.transform = 'scale(1)';
                        node.style.boxShadow = `0 0 8px ${point.speakerInfo?.color || '#ffffff'}`;
                    }
                }
            });

            // Highlight active thread paths
            const path = document.getElementById(`thread-path-${threadIndex}`);
            if (path) {
                const hasActivePoint = thread.points.some(point =>
                    Math.abs(point.time - currentTime) <= 3
                );

                if (hasActivePoint) {
                    path.style.opacity = '1';
                    path.style.filter = `drop-shadow(0 0 10px ${thread.color})`;
                } else {
                    path.style.opacity = '0.4';
                    path.style.filter = 'none';
                }
            }
        });

        // Highlight active tangents
        this.tangents.forEach((tangent, index) => {
            const path = document.getElementById(`tangent-arc-${index}`);
            const startMarker = document.getElementById(`tangent-marker-${index}-start`);
            const endMarker = document.getElementById(`tangent-marker-${index}-end`);

            const isActive = currentTime >= tangent.startTime && currentTime <= tangent.endTime;

            if (path) {
                path.style.opacity = isActive ? '1' : '0.5';
                path.style.strokeWidth = isActive ? '4' : '3';
            }

            if (startMarker) {
                startMarker.style.transform = isActive ? 'scale(1.2)' : 'scale(1)';
                startMarker.style.filter = isActive ? 'brightness(1.3)' : 'brightness(1)';
            }

            if (endMarker) {
                const nearEnd = currentTime > tangent.endTime - 1;
                endMarker.style.transform = (isActive && nearEnd) ? 'scale(1.2)' : 'scale(1)';
                endMarker.style.filter = (isActive && nearEnd) ? 'brightness(1.3)' : 'brightness(1)';
            }
        });
    }

    /**
     * Stop all running anime.js animations
     */
    stopAllAnimations() {
        if (typeof anime !== 'undefined' && anime.running) {
            // Get all running animations and pause/remove them
            const running = anime.running;
            for (let i = running.length - 1; i >= 0; i--) {
                running[i].pause();
            }
            // Clear the running array
            anime.running.length = 0;
        }
    }

    /**
     * Stop playback and reset highlights
     */
    stopPlayback() {
        this.isPlaying = false;
        
        // Stop all anime.js animations
        this.stopAllAnimations();
        
        if (this.animationFrameId) {
            clearTimeout(this.animationFrameId);
            this.animationFrameId = null;
        }

        const timeIndicator = document.getElementById('timeIndicator');
        if (timeIndicator) {
            timeIndicator.style.opacity = '0';
        }

        this.resetHighlights();
    }

    /**
     * Pause playback (alias for stopPlayback)
     */
    pausePlayback() {
        this.stopPlayback();
    }

    /**
     * Reset all visual highlights to default state
     */
    resetHighlights() {
        // Reset thread elements
        this.threads.forEach((thread, threadIndex) => {
            thread.points.forEach((point, pointIndex) => {
                const node = document.getElementById(`thread-node-${threadIndex}-${pointIndex}`);
                if (node) {
                    node.style.filter = 'brightness(1)';
                    node.style.boxShadow = `0 0 8px ${point.speakerInfo?.color || '#ffffff'}`;
                    node.style.transform = 'scale(1)';
                }
            });

            const path = document.getElementById(`thread-path-${threadIndex}`);
            if (path) {
                path.style.opacity = '0.7';
                path.style.filter = 'none';
            }
        });

        // Reset tangent elements
        this.tangents.forEach((tangent, index) => {
            const path = document.getElementById(`tangent-arc-${index}`);
            const startMarker = document.getElementById(`tangent-marker-${index}-start`);
            const endMarker = document.getElementById(`tangent-marker-${index}-end`);

            if (path) {
                path.style.opacity = '0.7';
                path.style.strokeWidth = '3';
            }
            if (startMarker) {
                startMarker.style.transform = 'scale(1)';
                startMarker.style.filter = 'brightness(1)';
            }
            if (endMarker) {
                endMarker.style.transform = 'scale(1)';
                endMarker.style.filter = 'brightness(1)';
            }
        });
    }

    /**
     * Seek to a specific time
     * @param {number} time - Time in seconds
     */
    seekToTime(time) {
        this.currentTime = time;
        const progress = time / this.totalDuration;

        const progressFill = document.getElementById('progressFill');
        const timeDisplay = document.getElementById('timeDisplay');
        const timeIndicator = document.getElementById('timeIndicator');

        if (progressFill) {
            progressFill.style.width = `${progress * 100}%`;
        }
        if (timeDisplay) {
            timeDisplay.textContent = `${formatTime(time)} / ${formatTime(this.totalDuration)}`;
        }

        if (timeIndicator) {
            const canvas = this.renderer.canvas;
            const canvasWidth = canvas.getBoundingClientRect().width;
            const padding = CONFIG.dimensions.canvasPadding;
            timeIndicator.style.left = `${padding + progress * (canvasWidth - 2 * padding)}px`;
            timeIndicator.style.opacity = '1';
        }

        this.highlightActiveElements(time);
    }
}
