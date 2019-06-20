import unittest

# Testing targets
from training_noodles.string_utils import (
    has_environment_variable, parse_requirement_expression, split_by_scheme)


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

    def test_invalid_expression(self):
        self.expr = '?abc'
        self.expected = None

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

    def test_invalid_scheme_1(self):
        self.s = 'scp user1@server1:~/file ~/file'
        self.schemes = ['local', 'remote']
        self.expected = (True, None, self.s)

    def test_invalid_scheme_2(self):
        self.s = 'export PATH=$HOME/program1:$HOME/program2'
        self.schemes = ['local', 'remote']
        self.expected = (True, None, self.s)

    def tearDown(self):
        # Split by scheme
        results = split_by_scheme(self.s, self.schemes)

        # Check the expected results
        self.assertEqual(results, self.expected)
