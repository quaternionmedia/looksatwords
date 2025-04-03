from datetime import datetime

from pandas import DataFrame

from .dataio import DataIO
from .hud import H, hud
from .llm import generate_news_description, generate_news_headline, host_url, publisher
from .validator import gnews_data_schema


class Generator(DataIO):
    """
    A base class for generating and validating data, inheriting from DataIO.

    Attributes:
        df_schema (Schema): Schema used for validating the dataframe.
        table_name (str): The name of the table used in the underlying data store, with a '_generator' suffix.
        n (int): Number of items to generate per batch.

    Methods:
        generate(): Placeholder method to be implemented in subclasses.
        validate(): Validates the current dataframe against the predefined pandera schema.
    """
    def __init__(self, db_path='data.json', table_name='generator', n=1):
        super().__init__(db_path=db_path, table_name=table_name)
        self.df_schema = gnews_data_schema
        self.table_name = self.table_name + '_generator'
        self.n = n

    def generate(self):
        pass

    def validate(self):
        self.df = self.df_schema.validate(self.df)
        return self.df


class GnewsGenerator(Generator):
    """
    A news generation class that uses language models to create news headlines and descriptions based on a seed word.

    Attributes:
        seedword (str): A keyword used as the seed for news content generation.
        table_name (str): The name of the table in the data store, with a '_gennews' suffix.

    Methods:
        generate(hud): Generates a batch of news items and returns them as a DataFrame.
        generate_news(hud): Generates a single news item including headline, description, and metadata.
        generate_news_batch(hud, task, n): Generates multiple news items and updates HUD progress.
    """
    def __init__(
        self, seedword=None, db_path='data.json', table_name='generatednews', **kwargs
    ):
        super().__init__(db_path=db_path, table_name=table_name, **kwargs)
        self.table_name = self.table_name + '_gennews'
        self.seedword = seedword

    @hud
    def generate(self, hud):
        """
        Generates a batch of news items and returns them as a DataFrame.
        Parameters:
            hud (Progress): The Rich progress tracker object for visualizing task progress.

        Returns:
            DataFrame: A DataFrame containing the generated news items with columns:
                       'headline', 'description', 'url', 'published date', 'publisher'.
        """
        columns = ['headline', 'description', 'url', 'published date', 'publisher']
        batch_generate_task = hud.add_task(
            f"[green]Generator:Generating {self.n} news...", total=self.n
        )
        news = self.generate_news_batch(n=self.n, task=batch_generate_task)
        self.df = DataFrame(news, columns=columns)
        return self.df

    @hud
    def generate_news(self, hud):
        """
        Generates a single news item including headline, description, and metadata.

        Parameters:
            hud (Progress): The Rich progress tracker object for task visualization.

        Returns:
            tuple: A tuple containing headline (str), description (str), url (str),
                   published date (str, ISO format), and publisher (str).
        """

        task_headline = hud.add_task(
            f"[green]Generator:Generating new headline", total=1
        )
        headline = generate_news_headline(seed=self.seedword)
        hud.update(task_headline, advance=1)
        task_description = hud.add_task(
            f"[green]Generator:Generating description for {headline[:16]}...", total=1
        )
        description = generate_news_description(headline)
        hud.update(task_description, advance=1)

        date = datetime.now().isoformat()
        url = host_url
        return headline, description, url, date, publisher

    @hud
    def generate_news_batch(self, hud, task, n=1):
        """
        Generates a batch of news items, updating a HUD task for each item generated.

        Parameters:
            hud (Progress): The Rich progress tracker object.
            task (TaskID): The task identifier for HUD progress tracking.
            n (int, optional): Number of news items to generate. Defaults to 1.

        Returns:
            list: A list of tuples, each containing generated news data.
        """
        news = []
        for _ in range(n):
            news.append(self.generate_news())
            hud.update(task, advance=1)

        return news
