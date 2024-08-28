from looksatwords.dataio import DataIO


def test_dataio_init():
    dataio = DataIO()
    assert dataio.df.empty
    assert dataio.table_name == 'io'

def test_dataio_saving():
    test_data = {'headline': 'test'}
    dataio = DataIO()
    dataio.df.insert(0, 'test', test_data)
    dataio.save()
    assert not dataio.df.empty
    loaded = dataio.load()
    assert not loaded.empty
    assert loaded.columns.tolist() == ['test']