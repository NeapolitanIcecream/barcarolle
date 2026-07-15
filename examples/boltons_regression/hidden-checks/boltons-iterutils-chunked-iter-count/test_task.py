from boltons.iterutils import chunked_iter


def test_chunked_iter_count_limits_chunks():
    assert list(chunked_iter(range(10), 3, count=2)) == [[0, 1, 2], [3, 4, 5]]


def test_chunked_iter_count_preserves_text_chunks():
    assert list(chunked_iter('abcdef', 2, count=2)) == ['ab', 'cd']


def test_chunked_iter_count_zero_yields_nothing():
    assert list(chunked_iter([1, 2, 3], 1, count=0)) == []
