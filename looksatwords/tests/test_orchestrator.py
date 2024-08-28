from looksatwords.orchestrator import Orchestrator
from looksatwords.gatherer import GnewsGatherer
from looksatwords.generator import GnewsGenerator

def test_orchestrator():
    g1 = GnewsGatherer()
    g2 = GnewsGatherer()
    f1 = GnewsGenerator()
    f2 = GnewsGenerator()
    orchestrator = Orchestrator()
    orchestrator.add_gatherers([g1, g2])
    orchestrator.gather()
    for g in orchestrator.gatherers:
        assert g.df is not None

    