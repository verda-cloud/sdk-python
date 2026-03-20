from verda.helpers import strip_none_values


def test_strip_none_values_removes_none_recursively():
    data = {
        'name': 'job',
        'optional': None,
        'nested': {
            'keep': 'value',
            'drop': None,
        },
        'items': [
            {'keep': 1, 'drop': None},
            None,
            ['value', None],
        ],
    }

    assert strip_none_values(data) == {
        'name': 'job',
        'nested': {'keep': 'value'},
        'items': [
            {'keep': 1},
            None,
            ['value', None],
        ],
    }
