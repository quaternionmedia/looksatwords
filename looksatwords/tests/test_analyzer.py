from looksatwords.analyzer import Analyzer
from looksatwords.gatherer import GnewsGatherer

def test_analyzer():
    gath = GnewsGatherer()
    gath.gather()
    a = Analyzer(dfs=[gath.df])
    a.build_words_df()
    a.preprocess()
    a.analyze()

    assert a.df is not None
    assert a.words_df is not None