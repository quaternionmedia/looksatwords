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
    """
    Parses a JSON object and converts it into a Rich Tree structure for display.

    Parameters:
        json (dict): A JSON-compatible dictionary representing hierarchical data.
        tree (rich.tree.Tree, optional): A Rich Tree object to populate. Defaults to a tree with root label 'db'.

    Returns:
        rich.tree.Tree: A tree visualization of the JSON structure, excluding any 'table' keys.
    """
    if isinstance(json, dict):
            for key, value in json.items():
                if key != 'table':
                    tree.add(f'{key}:{len(value)}')
            return tree


class HUD:
    """
    A terminal-based Heads-Up Display (HUD) for tracking and displaying task progress and JSON data using Rich.

    Attributes:
        title (str): The title displayed in the HUD header.
        refresh_per_second (int): The screen refresh rate for live updates.
        progress (rich.progress.Progress): A Rich Progress object to manage and display task progress.
        layout (rich.layout.Layout): A Rich Layout object managing the HUD's structure.
        live (rich.live.Live): Manages the live display of the HUD.

    Methods:
        __enter__(): Activates the live display context.
        __exit__(*args): Deactivates the live display context.
        show_db(path='data.json', level=1): Loads and displays a JSON database as a tree.
        make_layout(): Builds and returns the Rich Layout for the HUD.
        progress(): Returns the progress bar object.
    """
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
            screen=False,
        )

    def __enter__(self):
        self.live.__enter__()
        return self
    
    def __exit__(self, *args):
        self.live.__exit__(*args)

    

    def show_db(self, path='data.json', level=1):
        """
        Loads a JSON file and converts it into a Rich Tree structure for display.

        Parameters:
            path (str, optional): Path to the JSON file. Defaults to 'data.json'.
            level (int, optional): Not currently used. Reserved for potential future tree depth control.

        Returns:
            rich.tree.Tree: A Rich Tree representation of the JSON contents.
        """
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
        """
        Constructs the layout for the HUD using Rich's Layout and Panel classes.

        Returns:
            rich.layout.Layout: The structured layout containing header, progress display, database tree, and footer.
        """
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
        """
        Returns the Rich Progress object for external task tracking.

        Returns:
            rich.progress.Progress: The progress bar used to track tasks.
        """
        return self.progress

def get_hud():
    """
    Retrieves the singleton HUD instance. If it doesn't exist, creates one.

    Returns:
        HUD: The singleton HUD instance.
    """
    return H

H = HUD()

def hud(func):
    """
    Decorator that wraps a function to automatically enable the HUD live display context during execution.

    Parameters:
        func (callable): The function to be wrapped.

    Returns:
        callable: The wrapped function with live HUD display and injected progress tracking.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_hud().live as hud:
            return func(*args, hud=get_hud().progress, **kwargs)
    return wrapper