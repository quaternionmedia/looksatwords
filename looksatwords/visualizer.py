from wordcloud import WordCloud, get_single_color_func
from nltk import pos_tag
from PIL import Image
from numpy import array, pi
import matplotlib.pyplot as plt

from os import path, makedirs

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, LinearColorMapper, Whisker
from bokeh.transform import cumsum
from bokeh.io import output_file, save

import datetime

from .analyzer import Analyzer
from .validator import visualized_data_schema
from .hud import hud


class Visualizer(Analyzer):
    def __init__(self, db_path='dbs/data.json', output_path='output/'):
        super().__init__(db_path=db_path)
        self.df_schema = visualized_data_schema
        self.table_name = self.table_name + '_visualizer'
        self.output_path = output_path
        self.check_output_path()

    def check_output_path(self):
        if not path.exists(self.output_path):
            makedirs(self.output_path, exist_ok=True)

    def save_plot(self, plot, filename, wordcloud=False):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        folder_path = f'{self.output_path}{timestamp}/'
        makedirs(folder_path, exist_ok=True)
        output_file(f'{folder_path}{filename}.html')
        if wordcloud:
            plot.savefig(f'{folder_path}{filename}.png')
        else:
            save(plot)

    @hud
    def make_plots(self, hud):

        task = hud.add_task("[white]Visualizer:Making plots...", total=7)
        self.build_words_df()
        hud.update(task, advance=1)
        self.save_plot(word_cloud(self.words_df), 'word_cloud', wordcloud=True)
        hud.update(task, advance=1)
        self.save_plot(pie_cart_wordcount(self.words_df), 'word_count_pie')
        hud.update(task, advance=1)
        self.save_plot(plot_scatter_sentiment(self.df), 'scatter_sentiment')
        hud.update(task, advance=1)
        self.save_plot(plot_scatter(self.df), 'scatter')
        hud.update(task, advance=1)
        self.save_plot(plot_sentiment_scatter(self.df), 'sentiment_scatter')
        hud.update(task, advance=1)
        self.save_plot(boxplot(self.df), 'boxplot')
        hud.update(task, advance=1)
        return self.df
    
    def visualize(self):
        self.make_plots()
        return self.df


class GroupedColorFunc(object):
    """Create a color function object which assigns DIFFERENT SHADES of
       specified colors to certain words based on the color to words mapping.

       Uses wordcloud.get_single_color_func

       Parameters
       ----------
       color_to_words : dict(str -> list(str))
         A dictionary that maps a color to the list of words.

       default_color : str
         Color that will be assigned to a word that's not a member
         of any value from color_to_words.
    """

    def __init__(self, color_to_words, default_color):
        self.color_func_to_words = [
            (get_single_color_func(color), set(words))
            for (color, words) in color_to_words.items()]

        self.default_color_func = get_single_color_func(default_color)

    def get_color_func(self, word):
        """Returns a single_color_func associated with the word"""
        try:
            color_func = next(
                color_func for (color_func, words) in self.color_func_to_words
                if word in words)
        except StopIteration:
            color_func = self.default_color_func

        return color_func

    def __call__(self, word, **kwargs):
        return self.get_color_func(word)(word, **kwargs)



color_to_pos = {
    'blue': ['NN', 'NNS', 'NNP', 'NNPS'],
    'green': ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'],
    'red': ['JJ', 'JJR', 'JJS'],
    'orange': ['RB', 'RBR', 'RBS'],
    'purple': ['PRP', 'PRP$', 'WP', 'WP$'],
    'yellow': ['CC'],
    'pink': ['IN'],
    'brown': ['UH'],
}

def calculate_image_mask(file=None):
    if file is None:
        return None
    
    mask = array(Image.open(file))
    return mask


@hud
def word_cloud(df, hud):
    wc_task = hud.add_task("[white]Visualizer:Creating Word Cloud...", total=2)
    wordcloud = WordCloud(width=1000, height=750, max_font_size=1000, max_words=500, background_color='darkgrey', mask=calculate_image_mask())
    hud.update(wc_task, advance=1)
    wordcloud.generate_from_frequencies(frequencies=df['word'].value_counts().to_dict())
    hud.update(wc_task, advance=1)
    plt.figure(figsize=(15, 10))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    return plt

@hud
def pie_cart_wordcount(df, hud):
    wc_task = hud.add_task("[grey]Visualizer:Creating Word Count Pie Chart...", total=1)
    plot_df = df['word'].str.split(expand=True).stack().value_counts().reset_index().rename(columns={'index': 'word', 0: 'count'})
    plot_df['angle'] = plot_df['count']/plot_df['count'].sum() * 2*pi
    

    p = figure(height=350, title='Word Frequency', toolbar_location=None, tools='', min_width=600, min_height=400)
    p.wedge(x=0, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'), line_color=None, legend_field='word', source=plot_df)
    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None


    p.add_tools(HoverTool(tooltips=[('grey', '@word'), ('Count', '@count')]))
    hud.update(wc_task, advance=1)
    return p

@hud
def plot_scatter_sentiment(df, hud):
    plot_scatter_sentiment_task = hud.add_task("[grey]Visualizer:Creating Scatter Sentiment Plot...", total=1)
    source = ColumnDataSource(df)
    p = figure(min_width=1200, min_height=800)
    radii = df['headline_compound']
    color_mapper = LinearColorMapper(palette='Viridis256', low=min(radii), high=max(radii))
    p.scatter(x='headline_positive', y='headline_negative', source=source, fill_color={'field': 'headline_compound', 'transform': color_mapper}, size='headline_wordcount', line_color='black', line_width=0.5)
    p.xaxis.axis_label = 'Positivity'
    p.yaxis.axis_label = 'Negativity'
    p.title.text = 'Word Counts'
    p.add_tools(HoverTool(tooltips=[('Word', '@word'), ('Count', '@count')]))
    hud.update(plot_scatter_sentiment_task, advance=1)
    return p

@hud
def plot_scatter(df, hud):
    plot_scatter_task = hud.add_task("[grey]Visualizer:Creating Scatter Plot...", total=1)
    source = ColumnDataSource(df)
    p = figure(title='Sentiment Analysis', x_axis_label='Neutral', y_axis_label='Pos/Neg/Compound', min_width=800)
    p.scatter(x='headline_neutral', y='headline_positive', source=source, color='#14346499', size='headline_wordcount', legend_label='Positive')
    p.scatter(x='headline_neutral', y='headline_negative', source=source, color='#34146499', size='headline_wordcount', legend_label='Negative')
    p.scatter(x='headline_neutral', y='headline_compound', source=source, color='#46413499', size='headline_wordcount', legend_label='Compound')
    p.add_tools(HoverTool(tooltips=[('Word', '@word'), ('Count', '@count')]))
    hud.update(plot_scatter_task, advance=1)
    return p

@hud
def plot_sentiment_scatter(df, hud):
    plot_sentiment_scatter_task = hud.add_task("[grey]Visualizer:Creating Sentiment Scatter Plot...", total=1)
    p = figure(title='Sentiment Analysis', x_axis_label='Word Count', y_axis_label='Sentiment Score', min_width=800)
    p.scatter(x='headline_wordcount', y='headline_compound', source=ColumnDataSource(df), size='headline_wordcount', color='blue')
    hud.update(plot_sentiment_scatter_task, advance=1)
    return p

@hud
def boxplot(df, hud):
    boxplot_task = hud.add_task("[grey]Visualizer:Creating Boxplot...", total=1)
    p = figure(
        title='Boxplot for Sentiment Analysis of Article titles',
        x_range=df['headline'].unique(),
        x_axis_label='headline',
        y_axis_label='Sentiment Score',
        min_width=1200,

    )


    source = ColumnDataSource(df)

    headline_whisker = Whisker(source=source, base='headline', upper='headline_positive', lower='headline_negative', line_color='black')
    p.add_layout(headline_whisker)

    p.vbar(x='headline', top='headline_compound', bottom='headline_neutral', width=0.5, source=source, fill_color='blue', line_color='black')
    p.vbar(x='headline', top='headline_neutral', bottom='headline_negative', width=0.5, source=source, fill_color='green', line_color='black')

    p.scatter(x='headline', y='headline_compound', source=source, color='blue', legend_label='Compound')
    p.scatter(x='headline', y='headline_positive', source=source, color='green', legend_label='Positive')
    p.scatter(x='headline', y='headline_negative', source=source, color='red', legend_label='Negative')
    p.scatter(x='headline', y='headline_neutral', source=source, color='gray', legend_label='Neutral')
    p.add_tools(HoverTool(tooltips=[('Word', '@word'), ('Count', '@count')]))
    hud.update(boxplot_task, advance=1)
    return p