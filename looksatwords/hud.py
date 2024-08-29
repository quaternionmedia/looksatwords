from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn
from rich.spinner import Spinner
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.tree import Tree

from functools import wraps

import json

def parse_json_to_tree(json, tree=Tree('db')):
    if isinstance(json, dict):
            for key, value in json.items():
                if key != 'table':
                    tree.add(f'{key}:{len(value)}')
            return tree


class HUD:
    def __init__(self, title='Looking at words...'):
        self.title = title
        self.refresh_per_second = 4
        self.progress = Progress(
            SpinnerColumn('dots', style='blue'),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            BarColumn(),
            TextColumn("{task.description}"),

            # Only working for first few, then screen updates and all zeros
            TimeElapsedColumn(),
            TimeRemainingColumn(),

            expand=True,
            disable=True,
        )
        # self.console = Console()
        self.layout = self.make_layout()
        self.live = Live(
            self.layout,
            refresh_per_second=self.refresh_per_second,
            screen=True,
        )

    def __enter__(self):
        self.live.__enter__()
        return self
    
    def __exit__(self, *args):
        self.live.__exit__(*args)

    

    def show_db(self, path='data.json', level=1):
        try:
            with open(path, 'r') as f:
                db = json.load(f)
            return parse_json_to_tree(db)
        except:
            db = {}
            with open(path, 'w') as f:
                json.dump(db, f)
            return parse_json_to_tree(db)
    


    def make_layout(self):
        layout = Layout(
             name="root",
        )
        layout.split(
            Layout(name="header",size=3),
            Layout(name="main", ratio=3),
            Layout(name="footer", size=1),
        )
        layout["header"].split_row(
            Panel(Spinner("earth", text=f"[blue]{self.title}", style="blue")),
        )
        layout['main'].split_column(
             Layout(Panel(self.progress), name="progress", ratio=3),
             Layout(Panel(self.show_db()), name='db', ratio=1))
        layout["footer"].split_row(
            Spinner("bouncingBar", style="cyan"),
            Text("Ctrl-C twice to quit", style="bold blue"),
        )

        return layout

    def progress(self):
        return self.progress

def get_hud():
    return H

H = HUD()

def hud(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_hud().live as hud:
            return func(*args, hud=get_hud().progress, **kwargs)
    return wrapper