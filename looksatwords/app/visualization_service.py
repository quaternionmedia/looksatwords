"""Visualization service for generating plots and charts."""

import io
import base64
from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import Counter

from pydantic import BaseModel


class PlotRequest(BaseModel):
    """Request for generating a plot."""
    plot_type: str  # word_cloud, pie_chart, bar_chart, sentiment_scatter, word_frequency
    data: Optional[Dict[str, Any]] = None  # Additional plot-specific data
    width: int = 800
    height: int = 600
    title: Optional[str] = None


class PlotResponse(BaseModel):
    """Response containing plot data."""
    plot_type: str
    image_base64: Optional[str] = None
    html_content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class VisualizationService:
    """Service for generating visualizations."""
    
    def __init__(self):
        self._matplotlib_available = None
        self._wordcloud_available = None
        self._bokeh_available = None
    
    @property
    def matplotlib_available(self) -> bool:
        """Check if matplotlib is available."""
        if self._matplotlib_available is None:
            try:
                import matplotlib
                matplotlib.use('Agg')  # Use non-interactive backend
                import matplotlib.pyplot as plt
                self._matplotlib_available = True
            except ImportError:
                self._matplotlib_available = False
        return self._matplotlib_available
    
    @property
    def wordcloud_available(self) -> bool:
        """Check if wordcloud is available."""
        if self._wordcloud_available is None:
            try:
                from wordcloud import WordCloud
                self._wordcloud_available = True
            except ImportError:
                self._wordcloud_available = False
        return self._wordcloud_available
    
    @property
    def bokeh_available(self) -> bool:
        """Check if bokeh is available."""
        if self._bokeh_available is None:
            try:
                from bokeh.plotting import figure
                from bokeh.embed import file_html
                from bokeh.resources import CDN
                self._bokeh_available = True
            except ImportError:
                self._bokeh_available = False
        return self._bokeh_available
    
    def generate_word_cloud(
        self,
        words: List[str],
        width: int = 800,
        height: int = 400,
        background_color: str = "#1a1a2e",
        colormap: str = "viridis"
    ) -> PlotResponse:
        """Generate a word cloud from text.
        
        Args:
            words: List of words (can have duplicates for frequency)
            width: Image width
            height: Image height
            background_color: Background color
            colormap: Matplotlib colormap for colors
            
        Returns:
            PlotResponse with base64 encoded PNG
        """
        if not self.matplotlib_available or not self.wordcloud_available:
            return PlotResponse(
                plot_type="word_cloud",
                error="matplotlib or wordcloud not available"
            )
        
        import matplotlib.pyplot as plt
        from wordcloud import WordCloud
        
        # Count word frequencies
        word_freq = Counter(words)
        
        if not word_freq:
            return PlotResponse(
                plot_type="word_cloud",
                error="No words provided"
            )
        
        # Generate word cloud
        wc = WordCloud(
            width=width,
            height=height,
            background_color=background_color,
            colormap=colormap,
            max_words=100,
            min_font_size=10,
            max_font_size=100
        )
        wc.generate_from_frequencies(word_freq)
        
        # Convert to base64
        fig, ax = plt.subplots(figsize=(width/100, height/100))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', facecolor=background_color, edgecolor='none')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return PlotResponse(
            plot_type="word_cloud",
            image_base64=image_base64,
            data={"word_count": len(word_freq)}
        )
    
    def generate_word_frequency_chart(
        self,
        word_frequency: List[Dict[str, Any]],
        top_n: int = 20,
        title: str = "Word Frequency"
    ) -> PlotResponse:
        """Generate a horizontal bar chart of word frequencies.
        
        Args:
            word_frequency: List of {word: str, count: int}
            top_n: Number of top words to show
            title: Chart title
            
        Returns:
            PlotResponse with base64 encoded PNG
        """
        if not self.matplotlib_available:
            return PlotResponse(
                plot_type="bar_chart",
                error="matplotlib not available"
            )
        
        import matplotlib.pyplot as plt
        
        # Get top N words
        top_words = sorted(word_frequency, key=lambda x: x['count'], reverse=True)[:top_n]
        top_words.reverse()  # Reverse for horizontal bar chart
        
        words = [w['word'] for w in top_words]
        counts = [w['count'] for w in top_words]
        
        # Create chart
        fig, ax = plt.subplots(figsize=(10, max(6, len(words) * 0.3)))
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        
        colors = plt.cm.viridis([i/len(words) for i in range(len(words))])
        bars = ax.barh(words, counts, color=colors)
        
        ax.set_xlabel('Count', color='white')
        ax.set_title(title, color='white', fontsize=14)
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('#333')
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', facecolor='#1a1a2e')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return PlotResponse(
            plot_type="bar_chart",
            image_base64=image_base64,
            data={"words_shown": len(words)}
        )
    
    def generate_sentiment_chart(
        self,
        sentiment_data: List[Dict[str, Any]],
        title: str = "Sentiment Analysis"
    ) -> PlotResponse:
        """Generate a sentiment timeline/scatter chart.
        
        Args:
            sentiment_data: List of {time, compound, positive, negative, neutral, speaker}
            title: Chart title
            
        Returns:
            PlotResponse with base64 encoded PNG
        """
        if not self.matplotlib_available:
            return PlotResponse(
                plot_type="sentiment_scatter",
                error="matplotlib not available"
            )
        
        import matplotlib.pyplot as plt
        import numpy as np
        
        times = [d['time'] for d in sentiment_data]
        compounds = [d['compound'] for d in sentiment_data]
        positives = [d['positive'] for d in sentiment_data]
        negatives = [d['negative'] for d in sentiment_data]
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        fig.patch.set_facecolor('#1a1a2e')
        
        # Timeline chart
        ax1 = axes[0]
        ax1.set_facecolor('#1a1a2e')
        colors = ['#00ff88' if c > 0.05 else '#ff6b6b' if c < -0.05 else '#ffd93d' for c in compounds]
        ax1.scatter(times, compounds, c=colors, alpha=0.7, s=50)
        ax1.axhline(y=0, color='#666', linestyle='--', alpha=0.5)
        ax1.axhline(y=0.05, color='#00ff88', linestyle=':', alpha=0.3)
        ax1.axhline(y=-0.05, color='#ff6b6b', linestyle=':', alpha=0.3)
        ax1.set_xlabel('Time', color='white')
        ax1.set_ylabel('Compound Score', color='white')
        ax1.set_title('Sentiment Timeline', color='white')
        ax1.tick_params(colors='white')
        for spine in ax1.spines.values():
            spine.set_color('#333')
        
        # Positive vs Negative scatter
        ax2 = axes[1]
        ax2.set_facecolor('#1a1a2e')
        ax2.scatter(positives, negatives, c=compounds, cmap='RdYlGn', alpha=0.7, s=50)
        ax2.set_xlabel('Positive Score', color='white')
        ax2.set_ylabel('Negative Score', color='white')
        ax2.set_title('Positive vs Negative Sentiment', color='white')
        ax2.tick_params(colors='white')
        for spine in ax2.spines.values():
            spine.set_color('#333')
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', facecolor='#1a1a2e')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return PlotResponse(
            plot_type="sentiment_scatter",
            image_base64=image_base64
        )
    
    def generate_pos_pie_chart(
        self,
        pos_distribution: Dict[str, int],
        title: str = "Parts of Speech Distribution"
    ) -> PlotResponse:
        """Generate a pie chart of POS distribution.
        
        Args:
            pos_distribution: Dict of {pos_tag: count}
            title: Chart title
            
        Returns:
            PlotResponse with base64 encoded PNG
        """
        if not self.matplotlib_available:
            return PlotResponse(
                plot_type="pie_chart",
                error="matplotlib not available"
            )
        
        import matplotlib.pyplot as plt
        
        # Filter out zeros
        filtered = {k: v for k, v in pos_distribution.items() if v > 0}
        
        if not filtered:
            return PlotResponse(
                plot_type="pie_chart",
                error="No POS data available"
            )
        
        labels = list(filtered.keys())
        sizes = list(filtered.values())
        colors = plt.cm.Set3([i/len(labels) for i in range(len(labels))])
        
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            colors=colors,
            textprops={'color': 'white'}
        )
        
        ax.set_title(title, color='white', fontsize=14)
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', facecolor='#1a1a2e')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return PlotResponse(
            plot_type="pie_chart",
            image_base64=image_base64
        )
    
    def generate_speaker_comparison_chart(
        self,
        speaker_analytics: Dict[str, Any],
        title: str = "Speaker Comparison"
    ) -> PlotResponse:
        """Generate a comparison chart for speakers.
        
        Args:
            speaker_analytics: Dict of speaker -> analytics
            title: Chart title
            
        Returns:
            PlotResponse with base64 encoded PNG
        """
        if not self.matplotlib_available:
            return PlotResponse(
                plot_type="bar_chart",
                error="matplotlib not available"
            )
        
        import matplotlib.pyplot as plt
        import numpy as np
        
        speakers = list(speaker_analytics.keys())
        if not speakers:
            return PlotResponse(
                plot_type="bar_chart",
                error="No speaker data available"
            )
        
        messages = [speaker_analytics[s]['message_count'] for s in speakers]
        words = [speaker_analytics[s]['total_words'] for s in speakers]
        # Handle both dict and float formats for average_sentiment
        compounds = []
        for s in speakers:
            avg_sent = speaker_analytics[s].get('average_sentiment', 0)
            if isinstance(avg_sent, dict):
                compounds.append(avg_sent.get('compound', 0))
            else:
                compounds.append(avg_sent if isinstance(avg_sent, (int, float)) else 0)
        
        x = np.arange(len(speakers))
        width = 0.25
        
        fig, ax1 = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#1a1a2e')
        ax1.set_facecolor('#1a1a2e')
        
        bars1 = ax1.bar(x - width, messages, width, label='Messages', color='#00d4ff', alpha=0.8)
        bars2 = ax1.bar(x, [w/10 for w in words], width, label='Words (÷10)', color='#00ff88', alpha=0.8)
        
        ax1.set_xlabel('Speaker', color='white')
        ax1.set_ylabel('Count', color='white')
        ax1.set_title(title, color='white', fontsize=14)
        ax1.set_xticks(x)
        ax1.set_xticklabels(speakers, color='white')
        ax1.tick_params(colors='white')
        
        ax2 = ax1.twinx()
        ax2.bar(x + width, compounds, width, label='Sentiment', color='#ffd93d', alpha=0.8)
        ax2.set_ylabel('Sentiment Compound', color='white')
        ax2.tick_params(colors='white')
        
        for spine in ax1.spines.values():
            spine.set_color('#333')
        for spine in ax2.spines.values():
            spine.set_color('#333')
        
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', facecolor='#2a2a3e', edgecolor='#444', labelcolor='white')
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', facecolor='#1a1a2e')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return PlotResponse(
            plot_type="bar_chart",
            image_base64=image_base64
        )


# Singleton instance
_visualization_service = None


def get_visualization_service() -> VisualizationService:
    """Get or create the visualization service singleton."""
    global _visualization_service
    if _visualization_service is None:
        _visualization_service = VisualizationService()
    return _visualization_service
