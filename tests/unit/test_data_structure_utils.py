import collections
import unittest

# Testing targets
from training_noodles.data_structure_utils import (
    convert_values_to_strs, update_dict_with_missing, wrap_with_list)


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
            wrap_with_list(self.x)
