from boltons.cacheutils import LRI, LRU


def test_lri_update_accepts_keywords_only():
    cache = LRI(max_size=4)
    assert cache.update(alpha=1) is None
    assert cache['alpha'] == 1


def test_lru_update_accepts_keywords_only_and_preserves_capacity():
    cache = LRU(max_size=2)
    cache.update(alpha=1)
    cache.update([('beta', 2), ('gamma', 3)])
    assert 'alpha' not in cache
    assert cache['beta'] == 2
    assert cache['gamma'] == 3
