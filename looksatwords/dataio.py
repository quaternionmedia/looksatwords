from tinydb import TinyDB
from pandas import DataFrame
from os import path, makedirs
from rich import print

from .hud import hud

import time
def get_time():
    return time.strftime("%H:%M:%S", time.localtime())

def get_date():
    return time.strftime("%Y-%m-%d", time.localtime())

def get_datetime():
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())

def get_timestamp():
    return time.strftime("%Y%m%d%H%M%S", time.localtime())

class DataIO():

    def __init__(self, db_path='data.json', table_name='io'):
        self.df = DataFrame()
        self.db_path = db_path
        with open(db_path, 'a') as f:
            pass
        self.db = TinyDB(self.db_path) 
        self.table_name = table_name

    @hud
    def load(self, hud):
        # load_task = hud.add_task('[red]IO:Loading data...', total=1)
        # self.df = DataFrame(self.db.table(self.table_name).all())
        # hud.update(load_task,  advance=1)
        # return self.df
        load_task = hud.add_task('[red]IO:Loading data...', total=1)
        table = self.db.table(self.table_name)
        self.df = DataFrame(table.all())
        hud.update(load_task, advance=1)
        return self.df
    
    @hud
    def save(self, hud):
        save_task = hud.add_task('[red]IO:Saving data...', total=len(self.df))
        for i, row in self.df.iterrows():
            hud.update(save_task, advance=1)
            self.db.table(self.table_name).insert(row.to_dict())
        return self.df

    
    @hud
    def clear(self, hud):
        clear_task = hud.add_task('[red]IO:Clearing data...', total=1)
        self.df = DataFrame()
        self.save()
        hud.update(clear_task, advance=1)
        return self.df