"""Backend version of ThreadVisualizer for API usage.

Integrates with NLTK-based analyzer for enhanced text analysis including
sentiment detection and grammar analysis.
"""

import re
from typing import Dict, List, Optional, Any

# Try to import NLTK components for enhanced analysis
try:
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize
    from nltk import pos_tag
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class ThreadVisualizerBackend:
    """Backend thread visualization engine (without DOM/animation).
    
    This class analyzes conversation text to identify:
    - Speakers and their contributions
    - Topic threads based on keyword matching
    - Tangents (off-topic digressions) and their resolution
    - Optional: Sentiment analysis via NLTK
    """
    
    def __init__(self, use_nltk: bool = True):
        """Initialize the visualizer backend.
        
        Args:
            use_nltk: Whether to use NLTK for enhanced analysis (if available)
        """
        self.threads: List[Dict] = []
        self.tangents: List[Dict] = []
        self.timePoints: List[Dict] = []
        self.totalDuration: float = 0
        self.speakers: Dict[str, Dict] = {}
        self.use_nltk = use_nltk and NLTK_AVAILABLE
        
        # Initialize NLTK sentiment analyzer if available
        self._sia = None
        if self.use_nltk:
            try:
                self._sia = SentimentIntensityAnalyzer()
            except Exception:
                self._sia = None

        self.threadColors = [
            '#00d4ff', '#ff6b6b', '#00ff88', '#ffd93d', '#ff8cc8',
            '#a8e6cf', '#ffd3a5', '#fd6c9e', '#c1a1d3', '#84fab0'
        ]

        self.speakerColors = [
            '#ff6b6b', '#00d4ff', '#00ff88', '#ffd93d', '#ff8cc8',
            '#a8e6cf', '#ffd3a5', '#fd6c9e', '#c1a1d3', '#84fab0'
        ]

        self.topicKeywords = {
            'marketing': ['marketing', 'promotion', 'advertising', 'campaign', 'brand'],
            'technology': ['tech', 'digital', 'software', 'system', 'platform', 'online'],
            'environment': ['environment', 'green', 'sustainable', 'eco', 'climate', 'carbon'],
            'business': ['business', 'strategy', 'revenue', 'profit', 'growth', 'market'],
            'social': ['people', 'team', 'communication', 'relationship', 'community'],
            'finance': ['money', 'budget', 'cost', 'investment', 'financial', 'price'],
            'innovation': ['innovation', 'creative', 'new', 'idea', 'solution', 'future'],
            'quality': ['quality', 'excellence', 'standard', 'improvement', 'better']
        }

        self.tangentTriggers = [
            'but', 'however', 'wait', 'actually', 'speaking of', 'by the way',
            'side note', 'tangent', 'different subject', 'changing topics'
        ]

        self.resolutionKeywords = [
            'back to', 'returning to', 'anyway', 'so back to', 'as we were saying',
            'getting back', 'to return', 'where were we', "let's get back"
        ]

    def parseConversation(self, text: str) -> List[Dict]:
        """Parse conversation text into time points.
        
        Args:
            text: Raw conversation text with optional timestamps and speaker names
            
        Returns:
            List of parsed time points with metadata
        """
        lines = text.split('\n')
        timePoints = []
        self.speakers.clear()
        
        for index, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            timeInSeconds = index * 30  # Default 30 second spacing
            
            # Extract timestamp using regex
            ts_match = re.search(r'\[(\d+):(\d+)\]', line)
            if ts_match:
                timeInSeconds = int(ts_match.group(1)) * 60 + int(ts_match.group(2))
                line = re.sub(r'\[\d+:\d+\]', '', line).strip()
            
            # Extract speaker
            speaker = 'Unknown'
            cleanText = line
            
            if ':' in line:
                parts = line.split(':', 1)
                speaker = parts[0].strip()
                cleanText = parts[1].strip() if len(parts) > 1 else line
            
            if speaker not in self.speakers:
                speakerIndex = len(self.speakers)
                self.speakers[speaker] = {
                    'color': self.speakerColors[speakerIndex % len(self.speakerColors)],
                    'index': speakerIndex,
                    'contributions': 0
                }
            
            self.speakers[speaker]['contributions'] += 1
            
            # Analyze sentiment if NLTK available
            sentiment = None
            if self._sia:
                try:
                    sentiment = self._sia.polarity_scores(cleanText)
                except Exception:
                    sentiment = None
            
            timePoints.append({
                'time': timeInSeconds,
                'text': cleanText.lower(),
                'originalLine': line,
                'speaker': speaker,
                'speakerInfo': self.speakers[speaker],
                'index': index,
                'sentiment': sentiment
            })
        
        self.timePoints = sorted(timePoints, key=lambda p: p['time'])
        self.totalDuration = max([p['time'] for p in timePoints]) if timePoints else 0
        return timePoints

    def identifyThreads(self) -> List[Dict]:
        """Identify conversation threads by topic.
        
        Returns:
            List of identified threads sorted by total intensity
        """
        threads: Dict[str, Dict] = {}
        
        for point in self.timePoints:
            for threadName, keywords in self.topicKeywords.items():
                relevance = sum(1 for kw in keywords if kw in point['text'])
                
                if relevance > 0:
                    if threadName not in threads:
                        threads[threadName] = {
                            'name': threadName,
                            'points': [],
                            'color': self.threadColors[len(threads) % len(self.threadColors)],
                            'totalIntensity': 0
                        }
                    
                    thread = threads[threadName]
                    intensity = min(1.0, relevance * 0.3 + 0.2)
                    
                    # Include sentiment if available
                    point_data = {
                        'time': point['time'],
                        'intensity': intensity,
                        'text': point['originalLine'],
                        'speaker': point['speaker'],
                        'speakerInfo': point['speakerInfo']
                    }
                    
                    if point.get('sentiment'):
                        point_data['sentiment'] = point['sentiment']
                    
                    thread['points'].append(point_data)
                    thread['totalIntensity'] += intensity
        
        self.threads = sorted(
            [t for t in threads.values() if len(t['points']) >= 2],
            key=lambda t: t['totalIntensity'],
            reverse=True
        )[:8]
        
        self.detectTangents()
        return self.threads

    def detectTangents(self) -> List[Dict]:
        """Detect conversation tangents.
        
        Returns:
            List of detected tangent objects
        """
        self.tangents = []
        
        for index, point in enumerate(self.timePoints):
            hasTangentTrigger = any(
                trigger.lower() in point['text']
                for trigger in self.tangentTriggers
            )
            
            if hasTangentTrigger:
                tangent = self.analyzeTangent(point, index)
                if tangent:
                    self.tangents.append(tangent)
        
        return self.tangents

    def analyzeTangent(self, startPoint: Dict, startIndex: int) -> Optional[Dict]:
        """Analyze a single tangent.
        
        Args:
            startPoint: The starting time point
            startIndex: Index in timePoints array
            
        Returns:
            Tangent object or None
        """
        tangentTopics = self.getPointTopics(startPoint)
        
        endIndex = startIndex
        resolved = False
        resolutionPoint = None
        
        for i in range(startIndex + 1, len(self.timePoints)):
            point = self.timePoints[i]
            
            hasResolutionTrigger = any(
                keyword.lower() in point['text']
                for keyword in self.resolutionKeywords
            )
            
            if hasResolutionTrigger:
                resolved = True
                resolutionPoint = point
                endIndex = i
                break
            
            if i - startIndex > 2:
                endIndex = i - 1
                break
        
        if endIndex == startIndex:
            endIndex = min(startIndex + 1, len(self.timePoints) - 1)
        
        tangent_type = 'unresolved'
        if resolved:
            tangent_type = 'resolved'
        elif endIndex == startIndex or endIndex == startIndex + 1:
            tangent_type = 'orphaned'
        
        return {
            'startTime': startPoint['time'],
            'endTime': self.timePoints[endIndex]['time'] if endIndex < len(self.timePoints) else startPoint['time'] + 30,
            'startIndex': startIndex,
            'endIndex': endIndex,
            'type': tangent_type,
            'topics': tangentTopics,
            'resolutionPoint': resolutionPoint,
            'startText': startPoint['originalLine'],
            'resolutionText': resolutionPoint['originalLine'] if resolutionPoint else None
        }

    def getPointTopics(self, point: Dict) -> List[str]:
        """Get topics associated with a point.
        
        Args:
            point: Time point to analyze
            
        Returns:
            List of topic names found in the point
        """
        topics = []
        for threadName, keywords in self.topicKeywords.items():
            if any(kw in point['text'] for kw in keywords):
                topics.append(threadName)
        return topics

    def getAnalysisSummary(self) -> Dict[str, Any]:
        """Get a summary of the analysis results.
        
        Returns:
            Dictionary with analysis statistics
        """
        resolved_count = sum(1 for t in self.tangents if t['type'] == 'resolved')
        total_tangents = len(self.tangents)
        
        return {
            'speaker_count': len(self.speakers),
            'thread_count': len(self.threads),
            'tangent_count': total_tangents,
            'resolved_tangents': resolved_count,
            'unresolved_tangents': total_tangents - resolved_count,
            'resolution_rate': (resolved_count / total_tangents * 100) if total_tangents > 0 else 0,
            'total_duration': self.totalDuration,
            'time_point_count': len(self.timePoints),
            'nltk_enabled': self.use_nltk
        }
