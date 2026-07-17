from boltons.urlutils import QueryParamDict, parse_qsl


def test_parse_qsl_distinguishes_blank_from_bare():
    assert parse_qsl('empty=&bare&full=value') == [
        ('empty', ''),
        ('bare', None),
        ('full', 'value'),
    ]


def test_query_param_dict_round_trips_blank_and_bare_values():
    assert QueryParamDict.from_text('empty=&bare').to_text() == 'empty=&bare'


def test_parse_qsl_can_drop_blank_values():
    assert parse_qsl('empty=&bare&full=value', keep_blank_values=False) == [('full', 'value')]
