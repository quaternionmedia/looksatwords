from .dataio import DataIO
from .validator import gnews_data_schema
from .hud import hud, H

from pandas import DataFrame


class Generator(DataIO):
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

from datetime import datetime
from .llm import generate_news_headline, generate_news_description, host_url, publisher

class GnewsGenerator(Generator):
    def __init__(self, seedword=None, db_path='data.json', table_name='generatednews'):
        super().__init__(db_path=db_path, table_name=table_name)
        self.table_name = self.table_name + '_gennews'
        self.seedword = seedword
        
    @hud
    def generate(self, hud):
        columns = ['headline', 'description', 'url', 'published date', 'publisher']
        batch_generate_task = hud.add_task(f"[green]Generator:Generating {self.n} news...", total=self.n)
        news = self.generate_news_batch(self.n, task=batch_generate_task)
        self.df = DataFrame(news, columns=columns)
        return self.df
    
    @hud
    def generate_news(self, hud):

        task_headline = hud.add_task(f"[green]Generator:Generating new headline", total=1)
        headline = generate_news_headline(seed=self.seedword)
        hud.update(task_headline, advance=1)
        task_description = hud.add_task(f"[green]Generator:Generating description for {headline[:16]}...", total=1)
        description = generate_news_description(headline)
        hud.update(task_description, advance=1)

        date = datetime.now().isoformat()
        url = host_url
        return headline, description, url, date, publisher

    @hud
    def generate_news_batch(self, n, hud, task):
        news = []
        for _ in range(n):
            news.append(self.generate_news())
            hud.update(task, advance=1)

        return news