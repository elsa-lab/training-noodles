import copy
import unittest

# Testing targets
from training_noodles.spec import (
    _fill_missing_with_defaults, _fill_missing_in_stage_specs,
    _fill_missing_in_server_specs)


class TestFillMissingWithDefaults(unittest.TestCase):
    def setUp(self):
        # Set the default spec
        self.default_spec = {
            'number': 3,
            'string': 'three',
            'list': [1, 2, 3],
            'dict': {
                'one': 1,
                'two': 2,
                'three': {
                    'a': 1,
                    'b': 2,
                    'c': 3,
                },
            },
        }

        # Initialize the expected user spec
        self.expected_user_spec = {}

    def test_empty_1(self):
        # Set the user spec
        self.user_spec = {}

        # Set the keys to copy
        self.keys_to_copy = ['number']

        # Set the expected user spec
        self.expected_user_spec['number'] = self.default_spec['number']

    def test_empty_2(self):
        # Set the user spec
        self.user_spec = {}

        # Set the keys to copy
        self.keys_to_copy = ['number', 'dict']

        # Set the expected user spec
        self.expected_user_spec['number'] = self.default_spec['number']
        self.expected_user_spec['dict'] = self.default_spec['dict']

    def test_empty_nested(self):
        # Set the user spec
        self.user_spec = {}

        # Set the keys to copy
        self.keys_to_copy = ['string', 'dict/one', 'dict/three/c']

        # Set the expected user spec
        self.expected_user_spec['string'] = self.default_spec['string']
        self.expected_user_spec['dict'] = {}
        self.expected_user_spec['dict']['one'] = \
            self.default_spec['dict']['one']
        self.expected_user_spec['dict']['three'] = {}
        self.expected_user_spec['dict']['three']['c'] = \
            self.default_spec['dict']['three']['c']

    def test_empty_all(self):
        # Set the user spec
        self.user_spec = {}

        # Set the keys to copy
        self.keys_to_copy = ['*']

        # Set the expected user spec
        self.expected_user_spec = self.user_spec

    def test_mixed_1(self):
        # Set the user spec
        self.user_spec = {
            'number': -1,
            'list': [-1, -1, -1],
            'dict': {
                'zero': 0,
            }
        }

        # Set the keys to copy
        self.keys_to_copy = ['number', 'string', 'list', 'dict']

        # Set the expected user spec
        self.expected_user_spec = copy.deepcopy(self.user_spec)
        self.expected_user_spec['string'] = self.default_spec['string']

    def test_mixed_2(self):
        # Set the user spec
        self.user_spec = {
            'dict': {
                'zero': 0,
                'three': {
                    'b': -1,
                }
            }
        }

        # Set the keys to copy
        self.keys_to_copy = ['number', 'string', 'list', 'dict/*']

        # Set the expected user spec
        self.expected_user_spec = copy.deepcopy(self.user_spec)
        self.expected_user_spec['number'] = self.default_spec['number']
        self.expected_user_spec['string'] = self.default_spec['string']
        self.expected_user_spec['list'] = self.default_spec['list']
        self.expected_user_spec['dict']['one'] = \
            self.default_spec['dict']['one']
        self.expected_user_spec['dict']['two'] = \
            self.default_spec['dict']['two']

    def tearDown(self):
        # Copy the original default spec
        orig_default_spec = copy.deepcopy(self.default_spec)

        # Fill missing values from default spec
        _fill_missing_with_defaults(
            self.default_spec, self.user_spec, self.keys_to_copy)

        # Check whether the default spec is untouched
        self.assertEqual(self.default_spec, orig_default_spec)

        # Check the expected user spec
        self.assertEqual(self.user_spec, self.expected_user_spec)


class TestFillMissingWithDefaultsOrder(unittest.TestCase):
    def setUp(self):
        # Set the default spec
        self.default_spec = {
            'envs': {
                'b': 2,
                'a': 1,
                'c': 3,
            },
        }

        # Set the keys to copy
        self.keys_to_copy = ['envs/*']

        # Initialize the expected envs
        self.expected_envs = [('b', 2), ('a', 1), ('c', 3)]

    def test_empty(self):
        self.user_spec = {}

    def test_add(self):
        # Set the user spec
        self.user_spec = {
            'envs': {
                'd': 4,
            }
        }

        # Insert the new expected item
        self.expected_envs.insert(0, ('d', 4))

    def test_mixed_1(self):
        # Set the user spec
        self.user_spec = {
            'envs': {
                'a': -1,
                'd': 4,
            }
        }

        # Set the expected envs
        self.expected_envs = [('a', -1), ('d', 4), ('b', 2), ('c', 3)]

    def test_mixed_2(self):
        # Set the user spec
        self.user_spec = {
            'envs': {
                'd': 4,
                'a': -1,
                'b': -2,
            }
        }

        # Set the expected envs
        self.expected_envs = [('d', 4), ('a', -1),
                              ('b', -2), ('c', 3)]

    def tearDown(self):
        # Fill missing values from default spec
        _fill_missing_with_defaults(
            self.default_spec, self.user_spec, self.keys_to_copy)

        # Get the envs from user spec
        envs = list(self.user_spec['envs'].items())

        # Check the order of expected envs
        self.assertEqual(envs, self.expected_envs)


class TestFillMissingInStageSpecs(unittest.TestCase):
    def setUp(self):
        # Set the initial user spec
        self.user_spec = {
            'experiment_default': {
                'name': '<default>',
                'envs': {
                    'one': 1,
                    'two': 2,
                },
            },
        }

        # Initialize the expected user spec
        self.expected_user_spec = copy.deepcopy(self.user_spec)

    def test_experiments(self):
        # Add experiments
        self.user_spec['experiments'] = self._get_stage_spec()

        # Update the expected user spec
        self.expected_user_spec['experiments'] = \
            self._get_expected_stage_spec()

    def test_stages(self):
        # Set stages to be tested
        stages = [
            'before_all_experiments',
            'experiments',
            'after_all_experiments',
        ]

        # Iterate each stage
        for stage in stages:
            # Add experiments
            self.user_spec[stage] = self._get_stage_spec()

            # Update the expected user spec
            self.expected_user_spec[stage] = self._get_expected_stage_spec()

    def tearDown(self):
        # Fill missing values from default spec
        _fill_missing_in_stage_specs(self.user_spec)

        # Check the expected user spec
        self.assertEqual(self.user_spec, self.expected_user_spec)

    def _get_stage_spec(self):
        # Return a list of experiments
        return [
            {},
            {
                'name': 'my',
            },
            {
                'envs': {
                    'zero': 0,
                    'one': -1,
                },
            },
        ]

    def _get_expected_stage_spec(self):
        # Get the default spec
        default_exp = self.user_spec['experiment_default']

        # Return a list of expected experiments after filling
        return [
            default_exp,
            {
                'name': 'my',
                'envs': {
                    'one': 1,
                    'two': 2,
                },
            },
            {
                'name': '<default>',
                'envs': {
                    'zero': 0,
                    'one': -1,
                    'two': 2,
                },
            },
        ]


class TestFillMissingInServerSpecs(unittest.TestCase):
    def setUp(self):
        # Set the initial user spec
        self.user_spec = {
            'server_default': {
                'private_key_path': '<path>',
                'port': 22,
            }
        }

        # Initialize the expected user spec
        self.expected_user_spec = copy.deepcopy(self.user_spec)

    def test_server_spec(self):
        # Add server specs
        self.user_spec['servers'] = [
            {},
            {
                'private_key_path': 'my/long/path/to/key',
            },
            {
                'private_key_path': 'my/long/path/to/key',
                'port': 64,
            },
        ]

        # Update the expected user spec
        self.expected_user_spec['servers'] = [
            {
                'private_key_path': '<path>',
                'port': 22,
            },
            {
                'private_key_path': 'my/long/path/to/key',
                'port': 22,
            },
            {
                'private_key_path': 'my/long/path/to/key',
                'port': 64,
            },
        ]

    def tearDown(self):
        # Fill missing values from default spec
        _fill_missing_in_server_specs(self.user_spec)

        # Check the expected user spec
        self.assertEqual(self.user_spec, self.expected_user_spec)


if __name__ == '__main__':
    unittest.main()
