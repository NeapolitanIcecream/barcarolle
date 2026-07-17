import pytest

from boltons.iterutils import windowed, windowed_iter


def test_windowed_rejects_zero_size():
    with pytest.raises(ValueError):
        windowed([1, 2], 0)


def test_windowed_iter_rejects_negative_size():
    with pytest.raises(ValueError):
        list(windowed_iter([1, 2], -1))


def test_windowed_existing_positive_behavior_still_works():
    assert windowed([1, 2], 2) == [(1, 2)]
