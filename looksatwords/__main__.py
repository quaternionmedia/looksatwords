from click import Option, Argument, option, command
from typing_extensions import Annotated

from trogon import tui

from .orchestrator import Orchestrator
from .gatherer import GnewsGatherer, GnewsQuery
from .generator import GnewsGenerator
from .analyzer import Analyzer
from .visualizer import Visualizer

from .logs import log

__all__ = [Orchestrator, GnewsGatherer, GnewsQuery, GnewsGenerator, Analyzer, Visualizer]

orchestrator = Orchestrator()


@tui()
@command()
@option('--keywords', '-k', multiple=True, help="Keywords to search for")
@option('--table', '-t', help="Table to save to")
@option('--num_gen', '-f', help="Number of articles to generate")
@option('--num_gath', '-g', help="Number of articles to gather")
@option('--analysis_level', '-a', help="Analysis level, either leave blank for none, or 'default' for default analysis")
@option('--visuals_out', '-v', multiple=True, help="Visuals to output, blank for none any of 'sentiment', 'wordcount', 'grammar'")
def cli(
        keywords: Annotated[list[str], Option] = ['test'],
        table:Annotated[str, Argument] = 'io',
        num_gen:Annotated[int, Argument] = 3,
        num_gath:Annotated[int, Argument] = 3,
        analysis_level: Annotated[str, Option] = 'default',
        visuals_out: Annotated[list[str], Option] = ['sentiment', 'wordcount', 'grammar']):
    
    """
    Orchestrates the gathering, generating, analyzing, and visualizing of articles.
    """
    orchestrator.add_gatherer(GnewsGatherer(table_name=table, q=GnewsQuery(keyword=' '.join(keywords)), n=num_gath))
    orchestrator.gather()
    orchestrator.save()

    orchestrator.add_generator(GnewsGenerator(seedword=' '.join(keywords), n=num_gen))
    orchestrator.generate()
    if analysis_level == 'default':
        orchestrator.analyze()
    if len(visuals_out) > 0:
        orchestrator.visualize()


if __name__ == '__main__':
    cli()