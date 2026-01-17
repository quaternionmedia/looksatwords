"""Dynamic topic extraction service using NLTK.

Extracts topics from conversation text using:
- Noun phrase extraction
- Word frequency analysis with TF-IDF-like scoring
- POS-based filtering (nouns, proper nouns)
- Collocation detection
"""

from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional, Any
import re
import math

try:
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk import pos_tag, ne_chunk
    from nltk.tree import Tree
    from nltk.collocations import BigramCollocationFinder
    from nltk.metrics import BigramAssocMeasures
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class TopicExtractor:
    """Extract topics dynamically from conversation text using NLTK."""
    
    def __init__(self):
        """Initialize the topic extractor."""
        self._lemmatizer = None
        self._stop_words = None
        
        if NLTK_AVAILABLE:
            try:
                self._lemmatizer = WordNetLemmatizer()
                self._stop_words = set(stopwords.words('english'))
                # Add conversation-specific stopwords
                self._stop_words.update([
                    'yeah', 'yes', 'no', 'okay', 'ok', 'oh', 'um', 'uh',
                    'like', 'just', 'really', 'actually', 'basically',
                    'think', 'know', 'say', 'said', 'get', 'got', 'go',
                    'going', 'want', 'need', 'thing', 'things', 'something',
                    'way', 'time', 'people', 'good', 'great', 'right',
                    'let', 'make', 'well', 'back', 'also', 'could', 'would'
                ])
            except Exception:
                pass
    
    def extract_topics(
        self,
        text: str,
        max_topics: int = 8,
        min_occurrences: int = 2
    ) -> List[Dict[str, Any]]:
        """Extract topics from text.
        
        Args:
            text: The conversation text to analyze
            max_topics: Maximum number of topics to return
            min_occurrences: Minimum times a topic must appear
            
        Returns:
            List of topic dictionaries with name, keywords, and score
        """
        if not NLTK_AVAILABLE or not self._lemmatizer:
            return self._fallback_extraction(text, max_topics)
        
        # Parse conversation into messages
        messages = self._parse_messages(text)
        
        # Extract candidate topics using multiple methods
        noun_phrases = self._extract_noun_phrases(messages)
        significant_nouns = self._extract_significant_nouns(messages)
        collocations = self._extract_collocations(text)
        named_entities = self._extract_named_entities(messages)
        
        # Combine and score topics
        topic_scores = self._score_topics(
            noun_phrases, 
            significant_nouns, 
            collocations, 
            named_entities,
            len(messages)
        )
        
        # Filter and rank topics
        topics = self._rank_topics(topic_scores, max_topics, min_occurrences)
        
        return topics
    
    def extract_topics_per_message(
        self,
        messages: List[Dict[str, Any]],
        topics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Associate topics with individual messages.
        
        Args:
            messages: List of parsed message dictionaries
            topics: List of extracted topics
            
        Returns:
            Messages with topic associations added
        """
        if not topics:
            return messages
        
        # Build keyword lookup
        topic_keywords = {}
        for topic in topics:
            for keyword in topic.get('keywords', [topic['name']]):
                topic_keywords[keyword.lower()] = topic['name']
        
        # Associate topics with messages
        for message in messages:
            text = message.get('text', '').lower()
            message_topics = []
            
            for keyword, topic_name in topic_keywords.items():
                if keyword in text:
                    if topic_name not in message_topics:
                        message_topics.append(topic_name)
            
            message['topics'] = message_topics
        
        return messages
    
    def _parse_messages(self, text: str) -> List[Dict[str, str]]:
        """Parse conversation text into message dictionaries."""
        messages = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove timestamp
            clean_line = re.sub(r'\[\d+:\d+\]', '', line).strip()
            
            # Extract speaker and text
            speaker = 'Unknown'
            msg_text = clean_line
            
            if ':' in clean_line:
                parts = clean_line.split(':', 1)
                speaker = parts[0].strip()
                msg_text = parts[1].strip() if len(parts) > 1 else clean_line
            
            messages.append({
                'speaker': speaker,
                'text': msg_text,
                'original': line
            })
        
        return messages
    
    def _extract_noun_phrases(self, messages: List[Dict]) -> Counter:
        """Extract noun phrases from messages."""
        noun_phrases = Counter()
        
        for message in messages:
            text = message.get('text', '')
            tokens = word_tokenize(text)
            tagged = pos_tag(tokens)
            
            # Extract noun phrases (sequences of adjectives + nouns)
            current_phrase = []
            for word, tag in tagged:
                if tag.startswith('JJ') or tag.startswith('NN'):
                    word_lower = word.lower()
                    if word_lower not in self._stop_words and len(word_lower) > 2:
                        lemma = self._lemmatizer.lemmatize(word_lower, 'n')
                        current_phrase.append(lemma)
                else:
                    if current_phrase:
                        phrase = ' '.join(current_phrase)
                        if len(phrase) > 3:
                            noun_phrases[phrase] += 1
                        # Also count individual nouns
                        for word in current_phrase:
                            if word not in self._stop_words:
                                noun_phrases[word] += 1
                        current_phrase = []
            
            # Don't forget the last phrase
            if current_phrase:
                phrase = ' '.join(current_phrase)
                if len(phrase) > 3:
                    noun_phrases[phrase] += 1
                for word in current_phrase:
                    if word not in self._stop_words:
                        noun_phrases[word] += 1
        
        return noun_phrases
    
    def _extract_significant_nouns(self, messages: List[Dict]) -> Counter:
        """Extract significant nouns using TF-IDF-like scoring."""
        # Document frequency (how many messages contain each word)
        doc_freq = Counter()
        # Term frequency (total occurrences)
        term_freq = Counter()
        
        for message in messages:
            text = message.get('text', '')
            tokens = word_tokenize(text.lower())
            tagged = pos_tag(tokens)
            
            message_words = set()
            for word, tag in tagged:
                # Only consider nouns and proper nouns
                if tag.startswith('NN') and len(word) > 2:
                    if word not in self._stop_words:
                        lemma = self._lemmatizer.lemmatize(word, 'n')
                        term_freq[lemma] += 1
                        message_words.add(lemma)
            
            for word in message_words:
                doc_freq[word] += 1
        
        # Calculate TF-IDF-like scores
        num_messages = len(messages)
        scores = Counter()
        
        for word, tf in term_freq.items():
            df = doc_freq[word]
            # IDF: prefer words that appear in multiple but not all messages
            if df > 0 and df < num_messages:
                idf = math.log(num_messages / df) + 1
                scores[word] = tf * idf
            elif df == num_messages and tf > 1:
                # Appears everywhere - still relevant but lower score
                scores[word] = tf * 0.5
        
        return scores
    
    def _extract_collocations(self, text: str) -> List[Tuple[str, str]]:
        """Extract significant word pairs (collocations)."""
        try:
            tokens = word_tokenize(text.lower())
            # Filter tokens
            filtered = [
                self._lemmatizer.lemmatize(w, 'n') 
                for w in tokens 
                if w.isalpha() and len(w) > 2 and w not in self._stop_words
            ]
            
            if len(filtered) < 4:
                return []
            
            finder = BigramCollocationFinder.from_words(filtered)
            finder.apply_freq_filter(2)  # Must appear at least twice
            
            # Get top collocations
            bigrams = finder.nbest(BigramAssocMeasures.likelihood_ratio, 10)
            return bigrams
        except Exception:
            return []
    
    def _extract_named_entities(self, messages: List[Dict]) -> Counter:
        """Extract named entities from messages."""
        entities = Counter()
        
        for message in messages:
            text = message.get('text', '')
            try:
                tokens = word_tokenize(text)
                tagged = pos_tag(tokens)
                tree = ne_chunk(tagged)
                
                for subtree in tree:
                    if isinstance(subtree, Tree):
                        entity = ' '.join(word for word, tag in subtree.leaves())
                        entity_type = subtree.label()
                        if entity_type in ('ORGANIZATION', 'GPE', 'PERSON', 'FACILITY'):
                            entities[entity.lower()] += 1
            except Exception:
                continue
        
        return entities
    
    def _score_topics(
        self,
        noun_phrases: Counter,
        significant_nouns: Counter,
        collocations: List[Tuple[str, str]],
        named_entities: Counter,
        num_messages: int
    ) -> Dict[str, Dict]:
        """Combine and score topics from different extraction methods."""
        topic_data = defaultdict(lambda: {
            'score': 0,
            'keywords': set(),
            'sources': set()
        })
        
        # Score noun phrases (weight: 1.5)
        for phrase, count in noun_phrases.items():
            if count >= 1:
                topic_data[phrase]['score'] += count * 1.5
                topic_data[phrase]['keywords'].add(phrase)
                topic_data[phrase]['sources'].add('noun_phrase')
        
        # Score significant nouns (weight: 2.0 - TF-IDF already weighted)
        for noun, score in significant_nouns.items():
            topic_data[noun]['score'] += score * 2.0
            topic_data[noun]['keywords'].add(noun)
            topic_data[noun]['sources'].add('tfidf')
        
        # Score collocations (weight: 3.0 - bigrams are strong signals)
        for word1, word2 in collocations:
            phrase = f"{word1} {word2}"
            topic_data[phrase]['score'] += 3.0
            topic_data[phrase]['keywords'].add(word1)
            topic_data[phrase]['keywords'].add(word2)
            topic_data[phrase]['sources'].add('collocation')
        
        # Score named entities (weight: 4.0 - very specific)
        for entity, count in named_entities.items():
            topic_data[entity]['score'] += count * 4.0
            topic_data[entity]['keywords'].add(entity)
            topic_data[entity]['sources'].add('named_entity')
        
        return topic_data
    
    def _rank_topics(
        self,
        topic_scores: Dict[str, Dict],
        max_topics: int,
        min_occurrences: int
    ) -> List[Dict[str, Any]]:
        """Rank and filter topics."""
        # Convert to list and sort by score
        topics = []
        for name, data in topic_scores.items():
            # Skip very short topics
            if len(name) < 3:
                continue
            
            # Normalize score to 0-1 range
            score = data['score']
            
            topics.append({
                'name': name.title(),  # Capitalize for display
                'keywords': list(data['keywords']),
                'score': score,
                'sources': list(data['sources'])
            })
        
        # Sort by score descending
        topics.sort(key=lambda t: t['score'], reverse=True)
        
        # Remove duplicates (topics that are substrings of higher-ranked topics)
        filtered = []
        seen_keywords = set()
        
        for topic in topics:
            name_lower = topic['name'].lower()
            
            # Check if this topic is a substring of an already-added topic
            is_duplicate = False
            for seen in seen_keywords:
                if name_lower in seen or seen in name_lower:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(topic)
                seen_keywords.add(name_lower)
                
                if len(filtered) >= max_topics:
                    break
        
        # Normalize scores relative to max
        if filtered:
            max_score = filtered[0]['score']
            for topic in filtered:
                topic['normalized_score'] = topic['score'] / max_score if max_score > 0 else 0
        
        return filtered
    
    def _fallback_extraction(self, text: str, max_topics: int) -> List[Dict[str, Any]]:
        """Fallback topic extraction without NLTK."""
        # Simple word frequency without NLTK
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Basic stopwords
        basic_stops = {
            'that', 'this', 'with', 'from', 'have', 'been', 'were', 'they',
            'their', 'what', 'when', 'where', 'which', 'there', 'about',
            'would', 'could', 'should', 'these', 'those', 'being', 'after',
            'before', 'between', 'under', 'over', 'into', 'through'
        }
        
        word_counts = Counter(w for w in words if w not in basic_stops)
        
        topics = []
        for word, count in word_counts.most_common(max_topics):
            topics.append({
                'name': word.title(),
                'keywords': [word],
                'score': count,
                'normalized_score': 1.0 if not topics else count / word_counts.most_common(1)[0][1],
                'sources': ['fallback']
            })
        
        return topics


# Singleton instance
_topic_extractor: Optional[TopicExtractor] = None


def get_topic_extractor() -> TopicExtractor:
    """Get or create the singleton TopicExtractor instance."""
    global _topic_extractor
    if _topic_extractor is None:
        _topic_extractor = TopicExtractor()
    return _topic_extractor
