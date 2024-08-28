from looksatwords.gatherer import GnewsGatherer

def test_gnews_gatherer():
    gnews_gatherer = GnewsGatherer()
    gnews_gatherer.get_news()
    df = gnews_gatherer.validate()
    assert not df.empty
    
