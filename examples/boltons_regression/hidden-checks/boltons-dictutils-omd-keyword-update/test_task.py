from boltons.dictutils import OrderedMultiDict


def test_ordered_multi_dict_update_accepts_keywords_only():
    omd = OrderedMultiDict([('existing', 1)])
    assert omd.update(new_value=2) is None
    assert omd.items(multi=True) == [('existing', 1), ('new_value', 2)]


def test_ordered_multi_dict_update_existing_iterable_behavior_remains():
    omd = OrderedMultiDict([('a', 1), ('b', 2)])
    omd.update([('a', 3), ('a', 4)])
    assert omd.getlist('a') == [3, 4]
    assert omd.get('b') == 2
