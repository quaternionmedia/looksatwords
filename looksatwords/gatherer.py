from gnews import GNews
from pandas import DataFrame, concat

from .dataio import DataIO
from .hud import hud
from .validator import gnews_data_schema


class Query:
    def __init__(
        self,
        keywords=[],
        source=None,
    ):
        self.keywords = keywords


class GnewsQuery(Query):
    """
    Defines a query structure for retrieving news using GNews.

    Parameters:
        keyword (str, optional): The keyword to search news for.
        top (bool, optional): If True, retrieves top headlines. Defaults to False.
        location (str, optional): Specifies the geographic location for news filtering.
        topic (str, optional): A predefined topic to filter news by.
        site (str, optional): Filters news results by a specific website.
        start_date (datetime, optional): Start date for date-based filtering.
        end_date (datetime, optional): End date for date-based filtering.

    Methods:
        __str__(): Returns a comma-separated string of all non-None query parameters.
    """

    def __init__(
        self,
        top=False,
        location=None,
        topic=None,
        site=None,
        start_date=None,
        end_date=None,
    ):
        self.top = top
        self.location = location
        self.topic = topic
        self.site = site
        self.start_date = start_date
        self.end_date = end_date

    def __str__(self):
        # return non none values
        return ", ".join([f"{k}" for k, v in self.__dict__.items() if v is not None])


class Gatherer(DataIO):
    """
    Base class for gathering data from various sources, extending the DataIO class.

    Parameters:
        db_path (str): Path to the database where data is stored.
        table_name (str): Name of the table used within the database.
        raw_data_schema (Schema, optional): Schema used to validate the incoming raw data.
        n (int, optional): Number of results to retrieve per query. Defaults to 1.

    Methods:
        validate(): Validates the internal DataFrame against the schema and returns it.
    """

    def __init__(self, db_path, table_name, raw_data_schema=None, n=1):
        super().__init__(db_path=db_path, table_name=table_name)
        self.df_schema = raw_data_schema
        self.table_name = str(table_name) + "_gatherer"
        self.query = (None,)
        self.n = n

    def validate(self):
        self.df = self.df_schema.validate(self.df)
        return self.df


class GnewsGatherer(Gatherer):
    """
    A class for gathering news articles using the GNews API.

    Parameters:
        q (GnewsQuery, optional): A GnewsQuery object specifying search parameters. Defaults to top news.
        db_path (str): Path to the database file. Defaults to 'data.json'.
        table_name (str): Name of the table for saving data. Defaults to 'gnews'.
        **kwargs: Additional keyword arguments passed to the base Gatherer class.

    Methods:
        gather(hud): Fetches news articles based on the initialized query, with HUD task tracking.
        get_news(...): Manually retrieves articles using keyword, location, topic, site, or top flag.
    """

    def __init__(
        self,
        q: GnewsQuery = GnewsQuery(top=True),
        db_path="data.json",
        table_name="gnews",
        **kwargs,
    ):
        super().__init__(db_path=db_path, table_name=table_name, **kwargs)
        self.df_schema = gnews_data_schema
        self.table_name = "gnews"
        self.gnews = GNews(max_results=self.n)
        self.query = q

    @hud
    def gather(self, hud):
        """
        Fetches news articles based on the current query configuration and updates progress via HUD.

        Parameters:
            hud: A progress interface for visually tracking tasks.

        Returns:
            df (pd.DataFrame): A DataFrame containing the gathered news articles.
        """
        n = sum(
            [
                1
                for k, value in self.query.__dict__.items()
                if value is not None and k is not None and value is not False
            ]
        )
        if self.query is not None:
            task_gather_batch = hud.add_task(
                f"[yellow]Gatherer:Gathering batch...", total=n
            )
            for k, value in self.query.__dict__.items():
                if value is not None and k is not None and value is not False:
                    task_gather = hud.add_task(
                        f"[yellow]Gatherer:Gathering {k}={value}...", total=1
                    )
                    self.df = DataFrame(self.gnews.get_news(f"{k}={value}"))
                    hud.update(task_gather, advance=1)
                    hud.update(task_gather_batch, advance=1)
        else:
            task_gather = hud.add_task(
                f"[yellow]{n}Gatherer:Gathering top articles...", total=1
            )
            self.df = DataFrame(self.gnews.get_top_news())
            hud.update(task_gather, advance=1)

        self.df.rename(columns={"title": "headline"}, inplace=True)
        return self.df

    def get_news(self, keyword=None, top=True, location=None, topic=None, site=None):
        """
        Retrieves news articles based on specified filtering parameters.

        Parameters:
            keyword (str, optional): Retrieves articles articles containing the specified keyword.
            top (bool, optional): If True, retrieves top articles articles. Defaults to True.
            location (str, optional): Region-based news filtering.
            topic (str, optional):  Topic filter. Valid topics are 'WORLD', 'NATION', 'BUSINESS', 'TECHNOLOGY', 'ENTERTAINMENT', 'SPORTS', 'SCIENCE', 'HEALTH'.
            site (str, optional): Specific news source site filter.

        Returns:
            df (pd.DataFrame): A DataFrame of concatenated articles retrieved based on parameters.
        """

        # hardcoded topics
        topics = [
            "WORLD",
            "NATION",
            "BUSINESS",
            "TECHNOLOGY",
            "ENTERTAINMENT",
            "SPORTS",
            "SCIENCE",
            "HEALTH",
        ]
        articles = []
        if keyword is not None:
            articles.append(DataFrame(self.gnews.get_news(keyword)))
        if top is not None:
            articles.append(DataFrame(self.gnews.get_top_news()))
        if location is not None:
            articles.append(DataFrame(self.gnews.get_news_by_location(location)))
        if topic is not None:
            topic = topic.upper()
            if topic not in topics:
                raise ValueError(
                    f"Invalid topic '{topic}'. Valid topics are: {', '.join(topics)}"
                )
            articles.append(DataFrame(self.gnews.get_news_by_topic(topic)))
        if site is not None:
            articles.append(DataFrame(self.gnews.get_news_by_site(site)))

        self.df = concat(articles)

        self.df.rename(columns={"title": "headline"}, inplace=True)
        return self.df
