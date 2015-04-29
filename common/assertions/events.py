
import json
import pprint


def assert_event_matches(expected, actual, strict=False):
    """
    Compare two event dictionaries.

    Fail if any discrepancies exist, and output the list of all discrepancies. The intent is to produce clearer
    error messages than "{ some massive dict } != { some other massive dict }", instead enumerating the keys that
    differ. Produces period separated "paths" to keys in the output, so "context.foo" refers to the following
    structure:

        {
            'context': {
                'foo': 'bar'  # this key, value pair
            }
        }

    By default, it only asserts that all fields specified in the first event also exist and have the same value in
    the second event. If the `strict` parameter is passed in it will also ensure that *only* the fields in the first
    event exist in the second event. For example::

        expected = {
            'a': 'b'
        }

        actual = {
            'a': 'b',
            'c': 'd'
        }

        assert_event_matches(expected, actual, strict=False)  # This will not raise an AssertionError
        assert_event_matches(expected, actual, strict=True)   # This *will* raise an AssertionError
    """
    differences = compare_events(expected, actual, strict)
    if len(differences) > 0:
        debug_info = [
            'Expected:',
            get_pretty_event_string(expected),
            'Actual:',
            get_pretty_event_string(actual),
        ]
        raise AssertionError('Unexpected event differences found:\n' + '\n'.join(differences + debug_info))


def check_event_match(expected, actual, strict, path=None):
    if path is None:
        path = []
    differences = []

    # Some events store their payload in a JSON string instead of a dict. Comparing these strings can be problematic
    # since the keys may be in different orders, so we parse the string here if we were expecting a dict.
    if not strict and path == ['event'] and isinstance(expected, dict) and isinstance(actual, basestring):
        actual = json.loads(actual)

    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = frozenset(expected.keys())
        actual_keys = frozenset(actual.keys())

        for key in (expected_keys - actual_keys):
            differences.append('Expected key "{0}" not found in actual'.format(_path_to_string(path + [key])))

        if strict:
            for key in (actual_keys - expected_keys):
                differences.append('Actual key "{0}" was unexpected and this is a strict comparison'.format(_path_to_string(path + [key])))

        for key in (expected_keys & actual_keys):
            child_differences = check_event_match(expected[key], actual[key], strict, path + [key])
            differences.extend(child_differences)

    elif expected != actual:
        differences.append('Values are not equal at "{path}": expected="{a}" and actual="{b}"'.format(
            path=_path_to_string(path),
            a=expected,
            b=actual
        ))

    return differences


def is_matching_event(expected_event, actual_event):
    return len(check_event_match(expected_event, actual_event)) == 0


def get_pretty_event_string(event):
    return pprint.pformat(event)


def _path_to_string(path):
    return '.'.join(path)