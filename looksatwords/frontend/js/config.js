/**
 * Configuration module for Conversation Thread Visualizer
 * Contains all constants, colors, keywords, and settings
 */

export const CONFIG = {
    // API Configuration
    api: {
        base: window.location.origin.includes('localhost') 
            ? 'http://localhost:8000'
            : window.location.origin,
        get endpoint() {
            return `${this.base}/api`;
        }
    },

    // Color palettes
    colors: {
        threads: [
            '#00d4ff', '#ff6b6b', '#00ff88', '#ffd93d', '#ff8cc8',
            '#a8e6cf', '#ffd3a5', '#fd6c9e', '#c1a1d3', '#84fab0'
        ],
        speakers: [
            '#ff6b6b', '#00d4ff', '#00ff88', '#ffd93d', '#ff8cc8',
            '#a8e6cf', '#ffd3a5', '#fd6c9e', '#c1a1d3', '#84fab0'
        ],
        tangents: {
            resolved: '#00ff88',
            unresolved: '#ff6b6b',
            orphaned: '#ffd93d'
        },
        ui: {
            primary: '#00d4ff',
            secondary: '#ff00ff',
            success: '#00ff88',
            warning: '#ffd93d',
            error: '#ff6b6b'
        }
    },

    // Visualization dimensions
    dimensions: {
        canvasPadding: 50,
        threadSpacing: 60,
        nodeMinSize: 12,
        nodeMaxSize: 20,
        timelineHeight: 40
    },

    // Animation settings
    animation: {
        pathDuration: 2000,
        nodeDuration: 600,
        tangentDuration: 1200,
        playbackSpeed: 100,  // ms per 0.5 time units
        easing: 'easeOutQuart'
    },

    // Topic detection keywords
    keywords: {
        topics: {
            'marketing': ['marketing', 'promotion', 'advertising', 'campaign', 'brand'],
            'technology': ['tech', 'digital', 'software', 'system', 'platform', 'online'],
            'environment': ['environment', 'green', 'sustainable', 'eco', 'climate', 'carbon'],
            'business': ['business', 'strategy', 'revenue', 'profit', 'growth', 'market'],
            'social': ['people', 'team', 'communication', 'relationship', 'community'],
            'finance': ['money', 'budget', 'cost', 'investment', 'financial', 'price'],
            'innovation': ['innovation', 'creative', 'new', 'idea', 'solution', 'future'],
            'quality': ['quality', 'excellence', 'standard', 'improvement', 'better']
        },
        tangentTriggers: [
            'but', 'however', 'wait', 'actually', 'speaking of', 'by the way',
            'side note', 'tangent', 'different subject', 'changing topics'
        ],
        resolutionTriggers: [
            'back to', 'returning to', 'anyway', 'so back to', 'as we were saying',
            'getting back', 'to return', 'where were we', 'let\'s get back'
        ]
    },

    // Default sample conversation
    sampleConversation: `[0:00] John: Let's discuss our marketing strategy for next quarter.
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
[6:30] John: Sarah's right. Anyway, back to our strategy - let's schedule follow-up meetings to develop this further.`
};

// Freeze config to prevent accidental modifications
Object.freeze(CONFIG.colors);
Object.freeze(CONFIG.dimensions);
Object.freeze(CONFIG.animation);
Object.freeze(CONFIG.keywords);
