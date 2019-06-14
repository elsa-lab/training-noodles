import collections
import datetime
import unittest

# Testing targets
from training_noodles.utils import (
    convert_unix_time_to_iso, convert_values_to_strs, get_resource_path,
    has_environment_variable, parse_requirement_expression, split_by_scheme,
    update_dict_with_missing, wrap_with_list)


class TestConvertUnixTimeToIso(unittest.TestCase):
    def test_unix_time_zero(self):
        self.unix_time = 0
        self.expected_iso = '1970-01-01T00:00:00+00:00'

    def test_unix_time_year_2000(self):
        self.unix_time = 946684800
        self.expected_iso = '2000-01-01T00:00:00+00:00'

    def test_unix_time_1G(self):
        self.unix_time = 1000000000
        self.expected_iso = '2001-09-09T01:46:40+00:00'

    def tearDown(self):
        # Convert Unix time to ISO time
        iso_time = convert_unix_time_to_iso(
            self.unix_time, tz=datetime.timezone.utc)

        # Check the expected ISO time
        self.assertEqual(iso_time, self.expected_iso)


class TestConvertValuesToStrs(unittest.TestCase):
    def test_empty(self):
        self.d = {}
        self.expected = {}

    def test_numbers(self):
        self.d = {'a': 1, 'b': 2, 'c': 3}
        self.expected = {'a': '1', 'b': '2', 'c': '3'}

    def test_mixed(self):
        self.d = {'a': 1, 'string': 'value', 'list': [1, 2, 3], 'none': None}
        self.expected = {'a': '1', 'string': 'value',
                         'list': '[1, 2, 3]', 'none': 'None'}

    def tearDown(self):
        # Convert values to strings
        converted = convert_values_to_strs(self.d)

        # Check the expected converted dict
        self.assertEqual(converted, self.expected)


class TestGetResourcePath(unittest.TestCase):
    def test_defaults(self):
        self.package = 'training-noodles'
        self.resource_name = 'training_noodles/specs/defaults.yml'

    def tearDown(self):
        # Get the resource path
        path = get_resource_path(self.package, self.resource_name)

        # Open the file
        with open(path, 'r'):
            pass


class TestHasEnvironmentVariable(unittest.TestCase):
    def test_no_env(self):
        self.expr = 'abc-123_456'
        self.expected = False

    def test_simple_env(self):
        self.expr = 'abc-$ENV-123'
        self.expected = True

    def test_curly_env(self):
        self.expr = 'abc-${ENV}-123'
        self.expected = True

    def test_array(self):
        self.expr = 'abc-${ENV[1]}-123'
        self.expected = True

    def tearDown(self):
        # Test if there are any environment variables
        has_env = has_environment_variable(self.expr)

        # Check the expected result
        self.assertEqual(has_env, self.expected)


class TestParseRequirementExpression(unittest.TestCase):
    def test_operator_equal(self):
        self.expr = '==abc'
        self.expected = {'operator': '==', 'value': 'abc'}

    def test_operator_not_equal(self):
        self.expr = '!=abc'
        self.expected = {'operator': '!=', 'value': 'abc'}

    def test_operator_less_than(self):
        self.expr = '<abc'
        self.expected = {'operator': '<', 'value': 'abc'}

    def test_operator_greater_than(self):
        self.expr = '>abc'
        self.expected = {'operator': '>', 'value': 'abc'}

    def test_operator_less_than_or_equal(self):
        self.expr = '<=abc'
        self.expected = {'operator': '<=', 'value': 'abc'}

    def test_operator_greater_than_or_equal(self):
        self.expr = '>=abc'
        self.expected = {'operator': '>=', 'value': 'abc'}

    def test_operator_integer_value(self):
        self.expr = '==3'
        self.expected = {'operator': '==', 'value': 3}

    def test_operator_float_value(self):
        self.expr = '==1.0'
        self.expected = {'operator': '==', 'value': 1.0}

    def tearDown(self):
        # Parse the requirement expression
        result = parse_requirement_expression(self.expr)

        # Check the type of value
        if result is not None and isinstance(result['value'], float):
            # Check the expected operator
            self.assertEqual(result['operator'], self.expected['operator'])
            # Check the expected float
            self.assertAlmostEqual(result['value'], self.expected['value'])
        else:
            # Check the expected result
            self.assertEqual(result, self.expected)


class TestSplitByScheme(unittest.TestCase):
    def test_no_scheme(self):
        self.s = 'abc 123'
        self.schemes = ['local', 'remote']
        self.expected = (True, None, self.s)

    def test_identifiable_scheme(self):
        self.s = 'local:abc 123'
        self.schemes = ['local', 'remote']
        self.expected = (True, 'local', 'abc 123')

    def test_unidentifiable_scheme(self):
        self.s = 'unknown:abc 123'
        self.schemes = ['local', 'remote']
        self.expected = (False, 'unknown', 'abc 123')

    def test_invalid_scheme(self):
        self.s = 'scp user1@server1:~/file ~/file'
        self.schemes = ['local', 'remote']
        self.expected = (True, None, self.s)

    def tearDown(self):
        # Split by scheme
        results = split_by_scheme(self.s, self.schemes)

        # Check the expected results
        self.assertEqual(results, self.expected)


class TestUpdateDictWithMissing(unittest.TestCase):
    def test_1_dict(self):
        self.ds = [
            {}
        ]
        self.expected = {}

    def test_2_dicts(self):
        self.ds = [
            {},
            {'a': 1},
        ]
        self.expected = {'a': 1}

    def test_3_dicts(self):
        self.ds = [
            {'a': 1, 'b': 2},
            {},
            {'a': -1, 'b': -1, 'c': -1},
        ]
        self.expected = {'a': 1, 'b': 2, 'c': -1}

    def tearDown(self):
        # Update dict with missing properties
        updated = update_dict_with_missing(*self.ds)

        # Check the expected dict
        self.assertEqual(updated, self.expected)


class TestUpdateDictWithMissingOrder(unittest.TestCase):
    def test_empty(self):
        self.ds = [
            collections.OrderedDict([('b', 2)]),
            collections.OrderedDict([('a', 1)]),
        ]
        self.expected = [('b', 2), ('a', 1)]

    def test_mixed(self):
        self.ds = [
            collections.OrderedDict([('a', 1), ('b', 2)]),
            collections.OrderedDict(),
            collections.OrderedDict([('a', -1), ('b', -1), ('c', -1)]),
        ]
        self.expected = [('a', 1), ('b', 2), ('c', -1)]

    def tearDown(self):
        # Update dict with missing properties
        updated = update_dict_with_missing(*self.ds)

        # Get the items as list
        items = list(updated.items())

        # Check the expected items
        self.assertEqual(items, self.expected)


class TestWrapWithList(unittest.TestCase):
    def test_str(self):
        self.x = 'abc'
        self.expected = ['abc']

    def test_list(self):
        self.x = ['abc', '123']
        self.expected = self.x

    def tearDown(self):
        # Wrap the object with list
        wrapped = wrap_with_list(self.x)

        # Check the expected result
        self.assertEqual(wrapped, self.expected)


class TestWrapWithListExceptions(unittest.TestCase):
    def test_unknown(self):
        self.x = 0

    def tearDown(self):
        with self.assertRaises(ValueError):
            # Wrap the object with list
            wrapped = wrap_with_list(self.x)