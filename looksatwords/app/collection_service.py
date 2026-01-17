"""Service for aggregating analytics across a collection of conversations.

Provides corpus-level analysis including:
- Aggregated sentiment across multiple conversations
- Combined word frequency analysis
- Speaker participation across corpus
- Comparative analysis between conversations
"""

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from .analytics_service import get_analytics_service, ConversationAnalyticsService
from .topic_service import get_topic_extractor


class CollectionAnalyticsService:
    """Service for analyzing collections of conversations."""
    
    def __init__(self):
        """Initialize the collection analytics service."""
        self.analytics_service = get_analytics_service()
        self.topic_extractor = get_topic_extractor()
    
    def aggregate_conversations(
        self,
        conversations: List[Dict],
        time_points_list: List[List[Dict]]
    ) -> Dict[str, Any]:
        """Aggregate analytics across multiple conversations.
        
        Args:
            conversations: List of conversation records from DB
            time_points_list: List of parsed time points for each conversation
            
        Returns:
            Dictionary containing aggregated analytics
        """
        if not conversations:
            return self._empty_collection_analytics()
        
        # Aggregate all analytics
        all_words = []
        all_pos_counts = Counter()
        sentiment_scores = []
        speaker_data = defaultdict(lambda: {
            'message_count': 0,
            'total_words': 0,
            'sentiment_sum': 0.0
        })
        conversation_summaries = []
        sentiment_distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
        total_messages = 0
        total_words = 0
        
        for conv, time_points in zip(conversations, time_points_list):
            if not time_points:
                continue
                
            # Analyze each conversation
            conv_analytics = self.analytics_service.analyze_conversation(time_points)
            agg = conv_analytics['aggregated']
            
            # Accumulate totals
            total_messages += agg['total_messages']
            total_words += agg['total_words']
            
            # Accumulate sentiment
            sentiment_scores.append(agg['average_sentiment'])
            
            # Track sentiment distribution
            if agg['overall_sentiment'] == 'positive':
                sentiment_distribution['positive'] += 1
            elif agg['overall_sentiment'] == 'negative':
                sentiment_distribution['negative'] += 1
            else:
                sentiment_distribution['neutral'] += 1
            
            # Accumulate word frequency
            for wf in agg['word_frequency']:
                all_words.extend([wf['word']] * wf['count'])
            
            # Accumulate POS counts
            for pos, count in agg['pos_distribution'].items():
                all_pos_counts[pos] += count
            
            # Accumulate speaker stats
            for speaker, stats in conv_analytics['speaker_analytics'].items():
                speaker_data[speaker]['message_count'] += stats['message_count']
                speaker_data[speaker]['total_words'] += stats['total_words']
                speaker_data[speaker]['sentiment_sum'] += (
                    stats['average_sentiment'] * stats['message_count']
                )
            
            # Create conversation summary
            conversation_summaries.append({
                'id': conv.get('id') or conv.id if hasattr(conv, 'id') else 0,
                'title': conv.get('title') or conv.title if hasattr(conv, 'title') else 'Untitled',
                'messages': agg['total_messages'],
                'words': agg['total_words'],
                'sentiment': agg['overall_sentiment'],
                'compound': agg['average_sentiment']['compound']
            })
        
        # Calculate averages
        num_convs = len(conversations)
        avg_sentiment = self._average_sentiment(sentiment_scores)
        overall_sentiment = self._sentiment_label(avg_sentiment['compound'])
        
        # Calculate word frequency across corpus
        word_freq = Counter(all_words).most_common(30)
        
        # Calculate speaker stats
        speaker_stats = {}
        for speaker, data in speaker_data.items():
            if data['message_count'] > 0:
                avg_sent = data['sentiment_sum'] / data['message_count']
                speaker_stats[speaker] = {
                    'message_count': data['message_count'],
                    'total_words': data['total_words'],
                    'average_sentiment': avg_sent,
                    'sentiment_label': self._sentiment_label(avg_sent),
                    'average_words_per_message': data['total_words'] / data['message_count']
                }
        
        return {
            'conversation_count': num_convs,
            'total_messages': total_messages,
            'total_words': total_words,
            'average_words_per_message': total_words / total_messages if total_messages > 0 else 0,
            'avg_sentiment': avg_sentiment,
            'overall_sentiment': overall_sentiment,
            'sentiment_distribution': sentiment_distribution,
            'word_frequency': [{'word': w, 'count': c} for w, c in word_freq],
            'pos_distribution': dict(all_pos_counts),
            'unique_speakers': len(speaker_stats),
            'speaker_stats': speaker_stats,
            'conversation_summaries': conversation_summaries,
        }
    
    def extract_common_topics(
        self,
        conversations: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Extract common topics across a collection of conversations.
        
        Args:
            conversations: List of conversation records
            
        Returns:
            List of topic dictionaries with cross-conversation statistics
        """
        if not self.topic_extractor:
            return []
        
        topic_counts = Counter()
        topic_data = {}
        
        for conv in conversations:
            text = conv.get('text') or (conv.text if hasattr(conv, 'text') else '')
            if not text:
                continue
            
            topics = self.topic_extractor.extract_topics(text, max_topics=10)
            
            for topic in topics:
                name = topic['name'].lower()
                topic_counts[name] += 1
                if name not in topic_data:
                    topic_data[name] = {
                        'name': topic['name'],
                        'keywords': topic['keywords'],
                        'total_score': 0,
                        'appearances': []
                    }
                topic_data[name]['total_score'] += topic['score']
                topic_data[name]['appearances'].append(
                    conv.get('id') or (conv.id if hasattr(conv, 'id') else 0)
                )
        
        # Build result with percentage
        total_convs = len(conversations)
        result = []
        for name, count in topic_counts.most_common(15):
            data = topic_data[name]
            result.append({
                'topic': data['name'],
                'count': count,
                'percentage': (count / total_convs * 100) if total_convs > 0 else 0,
                'keywords': data['keywords'][:5],
                'avg_score': data['total_score'] / count if count > 0 else 0,
                'conversation_ids': data['appearances']
            })
        
        return result
    
    def compare_conversations(
        self,
        conversations: List[Dict],
        time_points_list: List[List[Dict]]
    ) -> Dict[str, Any]:
        """Compare conversations within a collection.
        
        Args:
            conversations: List of conversation records
            time_points_list: List of parsed time points
            
        Returns:
            Comparison data for all conversations
        """
        if not conversations:
            return self._empty_comparison()
        
        comparison_data = []
        sentiment_comparison = []
        verbosity_comparison = []
        speaker_overlap = defaultdict(list)
        word_sets = []
        
        for conv, time_points in zip(conversations, time_points_list):
            if not time_points:
                continue
            
            conv_id = conv.get('id') or (conv.id if hasattr(conv, 'id') else 0)
            conv_title = conv.get('title') or (conv.title if hasattr(conv, 'title') else 'Untitled')
            
            analytics = self.analytics_service.analyze_conversation(time_points)
            agg = analytics['aggregated']
            
            # Track sentiment for comparison
            sentiment_comparison.append({
                'id': conv_id,
                'title': conv_title,
                'compound': agg['average_sentiment']['compound'],
                'label': agg['overall_sentiment']
            })
            
            # Track verbosity
            verbosity_comparison.append({
                'id': conv_id,
                'title': conv_title,
                'words_per_message': agg['average_words_per_message'],
                'total_words': agg['total_words']
            })
            
            # Track speakers
            for speaker in analytics['speaker_analytics'].keys():
                speaker_overlap[speaker].append(conv_id)
            
            # Track words for common word analysis
            words = set(wf['word'] for wf in agg['word_frequency'])
            word_sets.append((conv_id, words))
            
            comparison_data.append({
                'id': conv_id,
                'title': conv_title,
                'analytics': analytics
            })
        
        # Find common words (appearing in multiple conversations)
        word_appearances = Counter()
        for _, words in word_sets:
            for word in words:
                word_appearances[word] += 1
        
        common_words = [
            {'word': word, 'conversation_count': count}
            for word, count in word_appearances.most_common(20)
            if count > 1
        ]
        
        return {
            'conversations': comparison_data,
            'sentiment_comparison': sorted(
                sentiment_comparison, 
                key=lambda x: x['compound'], 
                reverse=True
            ),
            'verbosity_comparison': sorted(
                verbosity_comparison,
                key=lambda x: x['words_per_message'],
                reverse=True
            ),
            'speaker_overlap': dict(speaker_overlap),
            'common_words': common_words
        }
    
    def _average_sentiment(self, sentiment_scores: List[Dict]) -> Dict[str, float]:
        """Calculate average sentiment from list of scores."""
        if not sentiment_scores:
            return {'neg': 0.0, 'neu': 0.0, 'pos': 0.0, 'compound': 0.0}
        
        n = len(sentiment_scores)
        return {
            'neg': sum(s['neg'] for s in sentiment_scores) / n,
            'neu': sum(s['neu'] for s in sentiment_scores) / n,
            'pos': sum(s['pos'] for s in sentiment_scores) / n,
            'compound': sum(s['compound'] for s in sentiment_scores) / n,
        }
    
    def _sentiment_label(self, compound: float) -> str:
        """Convert compound score to label."""
        if compound >= 0.05:
            return 'positive'
        elif compound <= -0.05:
            return 'negative'
        return 'neutral'
    
    def _empty_collection_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure."""
        return {
            'conversation_count': 0,
            'total_messages': 0,
            'total_words': 0,
            'average_words_per_message': 0,
            'avg_sentiment': {'neg': 0.0, 'neu': 0.0, 'pos': 0.0, 'compound': 0.0},
            'overall_sentiment': 'neutral',
            'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
            'word_frequency': [],
            'pos_distribution': {},
            'unique_speakers': 0,
            'speaker_stats': {},
            'conversation_summaries': [],
        }
    
    def _empty_comparison(self) -> Dict[str, Any]:
        """Return empty comparison structure."""
        return {
            'conversations': [],
            'sentiment_comparison': [],
            'verbosity_comparison': [],
            'speaker_overlap': {},
            'common_words': []
        }


# Singleton instance
_collection_analytics_service: Optional[CollectionAnalyticsService] = None


def get_collection_analytics_service() -> CollectionAnalyticsService:
    """Get or create the singleton CollectionAnalyticsService instance."""
    global _collection_analytics_service
    if _collection_analytics_service is None:
        _collection_analytics_service = CollectionAnalyticsService()
    return _collection_analytics_service
