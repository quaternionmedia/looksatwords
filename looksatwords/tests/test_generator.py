from looksatwords.generator import GnewsGenerator

def test_generator():
    gnews_generator = GnewsGenerator()
    gnews_generator.generate()
    df = gnews_generator.validate()
    assert not df.empty
