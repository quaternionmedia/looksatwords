from .validator import gnews_data_schema
from .dataio import DataIO
from pandas import DataFrame, concat
from gnews import GNews

from .hud import hud

class GnewsQuery():
        def __init__(self,
                     keyword=None,
                        top=False,
                        location=None,
                        topic=None,
                        site=None,
                        start_date=None,
                        end_date=None):
            self.keyword = keyword
            self.top = top
            self.location = location
            self.topic = topic
            self.site = site
            self.start_date = start_date
            self.end_date = end_date

        def __str__(self):
            # return non none values
            return ', '.join([f'{k}' for k, v in self.__dict__.items() if v is not None])


class Gatherer(DataIO):
    def __init__(self, db_path, table_name, raw_data_schema=None, n=1):
        super().__init__(db_path=db_path, table_name=table_name)
        self.df_schema = raw_data_schema
        self.table_name = str(table_name) + '_gatherer'
        self.query = None,
        self.n = n

    def validate(self):
        self.df = self.df_schema.validate(self.df)
        return self.df


class GnewsGatherer(Gatherer):
    def __init__(self, q: GnewsQuery=GnewsQuery(top=True),
                   db_path='data.json',
                   table_name='gnews'
                   ):
        super().__init__(db_path=db_path, table_name=table_name)
        self.df_schema = gnews_data_schema
        self.table_name = 'gnews'
        self.gnews = GNews(max_results=self.n)
        self.query = q

    
    @hud
    def gather(self, hud):
        n = sum([1 for k, value in self.query.__dict__.items() if value is not None and k is not None and value is not False])
        if self.query is not None:
            task_gather_batch = hud.add_task(f"[yellow]Gatherer:Gathering batch...", total=n)
            for k, value in self.query.__dict__.items():
                if value is not None and k is not None and value is not False:
                    task_gather = hud.add_task(f"[yellow]Gatherer:Gathering {k}={value}...", total=1)
                    self.df = DataFrame(self.gnews.get_news(f'{k}={value}'))
                    hud.update(task_gather, advance=1)
                    hud.update(task_gather_batch, advance=1)
        else:
            task_gather = hud.add_task(f"[yellow]{ n }Gatherer:Gathering top articles...", total=1)
            self.df = DataFrame(self.gnews.get_top_news())
            hud.update(task_gather, advance=1)

        self.df.rename(columns={'title':'headline'}, inplace=True)
        return self.df
    
    
    def get_news(self, keyword=None, top=True, location=None, topic=None, site=None):
        """
        Retrieves articles articles based on specified parameters.
        Parameters:
        - keyword (str): Optional. Retrieves articles articles containing the specified keyword.
        - top (bool): Optional. If True, retrieves top articles articles.
        - location (str): Optional. Retrieves articles articles from the specified location.
        - topic (str): Optional. Retrieves articles articles from the specified topic. Valid topics are 'WORLD', 'NATION', 'BUSINESS', 'TECHNOLOGY', 'ENTERTAINMENT', 'SPORTS', 'SCIENCE', 'HEALTH'.
        - site (str): Optional. Retrieves articles articles from the specified site.
        Returns:
        - DataFrame: A DataFrame containing the retrieved articles articles.
        """
        
        # hardcoded topics
        topics =  ['WORLD', 'NATION', 'BUSINESS', 'TECHNOLOGY', 'ENTERTAINMENT', 'SPORTS', 'SCIENCE', 'HEALTH']
        articles = []
        if keyword is not None:
            articles.append(DataFrame(self.gnews.get_news(keyword)))
        if top is not None:
            articles.append(DataFrame(self.gnews.get_top_news()))
        if location is not None:
            articles.append(DataFrame(self.gnews.get_news_by_location(location)))
        if topic is not None and topic in topics:
            topic = topic.upper()
            articles.append(DataFrame(self.gnews.get_news_by_topic(topic)))
        if site is not None:
            articles.append(DataFrame(self.gnews.get_news_by_site(site)))
        
        self.df = concat(articles)

        self.df.rename(columns={'title':'headline'}, inplace=True)
        return self.df