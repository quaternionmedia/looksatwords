from tinydb import TinyDB
from pandas import DataFrame
from os import path, makedirs
from rich import print

from .hud import hud

import time


def get_time():
    """
    Returns the current local time formatted as HH:MM:SS.

    Returns:
        str: The current time.
    """
    return time.strftime("%H:%M:%S", time.localtime())


def get_date():
    """
    Returns the current local date formatted as YYYY-MM-DD.

    Returns:
        str: The current date.
    """
    return time.strftime("%Y-%m-%d", time.localtime())


def get_datetime():
    """
    Returns the current local date and time formatted as YYYY-MM-DD_HH:MM:SS.

    Returns:
        str: The current date and time.
    """
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())


def get_timestamp():
    """
    Returns a timestamp in the format YYYYMMDDHHMMSS.

    Returns:
        str: The current timestamp.
    """
    return time.strftime("%Y%m%d%H%M%S", time.localtime())


class DataIO:
    """
    A base class for managing data I/O operations using TinyDB and pandas DataFrames.

    Parameters:
        db_path (str): The file path to the TinyDB database. Defaults to 'data.json'.
        table_name (str): The name of the table to read from and write to. Defaults to 'io'.

    Attributes:
        df (pd.DataFrame): The in-memory DataFrame used for data manipulation.
        db_path (str): File path to the TinyDB file.
        db (TinyDB): The TinyDB database object.
        table_name (str): The name of the TinyDB table used for data storage.
    """

    def __init__(self, db_path="data.json", table_name="io"):
        self.df = DataFrame()
        self.db_path = db_path
        with open(db_path, "a") as f:
            pass
        self.db = TinyDB(self.db_path)
        self.table_name = table_name

    @hud
    def load(self, hud):
        """
        Loads data from the TinyDB table into a pandas DataFrame.

        Parameters:
            hud: A HUD object for tracking progress visually.

        Returns:
            pd.DataFrame: The DataFrame containing the loaded data.
        """
        load_task = hud.add_task("[red]IO:Loading data...", total=1)
        table = self.db.table(self.table_name)
        self.df = DataFrame(table.all())
        hud.update(load_task, advance=1)
        return self.df

    @hud
    def save(self, hud):
        """
        Saves the current DataFrame to the TinyDB table.

        Parameters:
            hud: A HUD object for tracking progress visually.

        Returns:
            pd.DataFrame: The DataFrame that was saved.
        """
        save_task = hud.add_task("[red]IO:Saving data...", total=len(self.df))
        for i, row in self.df.iterrows():
            hud.update(save_task, advance=1)
            self.db.table(self.table_name).insert(row.to_dict())
        return self.df

    @hud
    def clear(self, hud):
        """
        Clears the current DataFrame and overwrites the table in TinyDB with an empty one.

        Parameters:
            hud: A HUD object for tracking progress visually.

        Returns:
            pd.DataFrame: An empty DataFrame.
        """
        clear_task = hud.add_task("[red]IO:Clearing data...", total=1)
        self.df = DataFrame()
        self.save()
        hud.update(clear_task, advance=1)
        return self.df
