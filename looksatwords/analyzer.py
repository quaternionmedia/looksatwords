from .gatherer import GnewsGatherer

from .validator import analyzed_data_schema

from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer

from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from string import punctuation

from pandas import concat, DataFrame

from .hud import hud


# Initialize NLTK components
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
sia = SentimentIntensityAnalyzer()


class Analyzer(GnewsGatherer):
    def __init__(self,
                 db_path='data.json',
                 dfs=None,
                 analyzis_level='default'):
        super().__init__(db_path=db_path, table_name='analyzer')
        self.df_schema = analyzed_data_schema
        self.table_name = self.table_name + '_analyzer'
        self.words_df = None
        if dfs is not None:
            for df in dfs:
                self.combine(df)

    @hud
    def build_words_df(self, hud):
        words = []
        task = hud.add_task("[purple]Analyzer:Building words DataFrame...", total=2*len(self.df))
        for headline in self.df['headline']:
            words.extend(headline.split())
            hud.update(task, advance=1)
        for description in self.df['description']:
            words.extend(description.split())
            hud.update(task, advance=1)
        self.words_df = DataFrame(words, columns=['word'])
        self.words_df['word'] = self.words_df['word'].apply(lambda x: x.lower())
        return self.words_df
    
    @hud
    def preprocess(self, hud):
        task = hud.add_task("[purple]Analyzer:Preprocessing data...", total=len(self.df))
        for i, row in self.df.iterrows():
            self.df.at[i, 'headline'] = clean_text(row['headline'])
            self.df.at[i, 'headline_cleaned'] = preprocess_text(row['headline'])
            self.df.at[i, 'description_cleaned'] = preprocess_text(row['description'])
            hud.update(task, advance=1)
        return self.df
    

    @hud
    def analyze(self, hud):
        to_process = ['headline', 'description']
        task = hud.add_task("[purple]Analyzer:Analyzing data...", total=3*len(to_process))
        for column in to_process:
            hud.update(task, description=f"[purple]Analyzer:Analyzing {column}...")
            apply_preprocessing_and_sentiment_analysis(self.df, f'{column}_cleaned', column)
            hud.update(task, advance=1)
            hud.update(task, description=f"[purple]Analyzer:Counting words in {column}...")
            apply_wordcount(self.df, f'{column}_cleaned', column)
            hud.update(task, advance=1)
            hud.update(task, description=f"[purple]Analyzer:Analyzing grammar in {column}...")
            apply_grammar_analysis(self.df, f'{column}_cleaned', column)
            hud.update(task, advance=1)

        return self.df
    
    def combine(self, df):
        self.df = concat([self.df, df])
        return self.df

def get_wordnet_pos(treebank_tag):
    """Map POS tag to first character used by WordNetLemmatizer"""
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN  # by default, treat as noun

def preprocess_text(text):
    tokens = word_tokenize(text)
    tokens = [word.lower() for word in tokens]
    tokens = [word for word in tokens if word.isalpha() or word in punctuation]
    pos_tags = pos_tag(tokens)
    tokens = [lemmatizer.lemmatize(word, get_wordnet_pos(pos)) for word, pos in pos_tags]
    tokens = [word for word in tokens if word not in stop_words]
    return " ".join(tokens)

def get_sentiment_scores(text):
    return sia.polarity_scores(text)

def analyze_sentiment(headline):
    sentiment_analyzer = SentimentIntensityAnalyzer()
    return sentiment_analyzer.polarity_scores(headline)

def clean_text(text):
    # Remove stopwords
    text = ' '.join([word for word in text.split() if word.lower() not in stop_words])
    # Remove publisher title from headline
    text = text.split(' - ')[0]
    # Retain only first line
    text = text.split('\n')[0]
    # Lemmatize words
    text = ' '.join([lemmatizer.lemmatize(word) for word in text.split()])
    # Remove punctuation
    text = text.replace('[^\w\s]', '')
    # Remove extra spaces
    text = ' '.join(text.split())
    # Remove hyphens
    text = text.replace('-', ' ')
    return text


def apply_sentiment_analysis(df, column_name, prefix):
    df[f'{prefix}_sentiment'] = df[column_name].apply(get_sentiment_scores)
    df[f'{prefix}_positive'] = df[f'{prefix}_sentiment'].apply(lambda x: float(x['pos']))
    df[f'{prefix}_negative'] = df[f'{prefix}_sentiment'].apply(lambda x: float(x['neg']))
    df[f'{prefix}_neutral'] = df[f'{prefix}_sentiment'].apply(lambda x: float(x['neu']))
    df[f'{prefix}_compound'] = df[f'{prefix}_sentiment'].apply(lambda x: float(x['compound']))

def apply_wordcount(df, column_name, prefix):
    df[f'{prefix}_wordcount'] = df[column_name].apply(lambda x: len(x.split()))

@hud
def apply_preprocessing_and_sentiment_analysis(df, column_name, prefix, hud):
    pre_task = hud.add_task(f"[purple]Analyzer:Preprocessing {prefix}...", total=1)
    df[f'abstracted_{prefix}'] = df[column_name].apply(preprocess_text)
    hud.update(pre_task, advance=1)
    sentiment_task = hud.add_task(f"[purple]Analyzer:Analyzing sentiment in {prefix}...", total=1)
    apply_sentiment_analysis(df, f'{prefix}_cleaned', prefix)
    hud.update(sentiment_task, advance=1)
    wordcount_task = hud.add_task(f"[purple]Analyzer:Counting words in {prefix}...", total=1)
    apply_wordcount(df, f'{prefix}_cleaned', prefix)
    hud.update(wordcount_task, advance=1)

pos = {
    'NN': 'Noun',
    'NNS': 'Noun',
    'NNP': 'Noun',
    'NNPS': 'Noun',
    'VB': 'Verb',
    'VBD': 'Verb',
    'VBG': 'Verb',
    'VBN': 'Verb',
    'VBP': 'Verb',
    'VBZ': 'Verb',
    'JJ': 'Adjective',
    'JJR': 'Adjective',
    'JJS': 'Adjective',
    'RB': 'Adverb',
    'RBR': 'Adverb',
    'RBS': 'Adverb',
    'PRP': 'Pronoun',
    'PRP$': 'Pronoun',
    'WP': 'Pronoun',
    'WP$': 'Pronoun',
    'CC': 'Conjunction',
    'IN': 'Preposition',
    'UH': 'Interjection',
}

pos_groups = {
    'Noun': ['NN', 'NNS', 'NNP', 'NNPS'],
    'Verb': ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'],
    'Adjective': ['JJ', 'JJR', 'JJS'],
    'Adverb': ['RB', 'RBR', 'RBS'],
    'Pronoun': ['PRP', 'PRP$', 'WP', 'WP$'],
    'Conjunction': ['CC'],
    'Preposition': ['IN'],
    'Interjection': ['UH'],
}

def apply_grammar_analysis(df, column_name, prefix):
    for pos_group, pos_tags in pos_groups.items():
        df[f'{prefix}_{pos_group.lower()}'] = df[column_name].apply(lambda x: len([word for word, pos in pos_tag(word_tokenize(x)) if pos in pos_tags]))
