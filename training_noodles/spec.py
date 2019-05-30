import json
import logging

import yaml


def read_user_spec(args):
    # Set the path to default spec
    default_spec_path = 'training_noodles/specs/defaults.yml'

    # Split the spec into spec path and experiments spec
    user_spec_path, experiments = _split_path_and_experiments(args.spec)

    # Read the default spec
    default_spec = _read_spec(default_spec_path)

    # Read the user spec
    user_spec = _read_spec(user_spec_path)

    # Fill missing values with default values
    _fill_missing_with_defaults(default_spec, user_spec)

    # Filter the experiments
    _filter_experiments(user_spec, experiments)

    # Log the user spec
    logging.debug('User spec->\n{}'.format(json.dumps(user_spec)))

    # Return the filled user spec
    return user_spec


def _read_spec(path):
    try:
        with open(path, 'r') as stream:
            spec_data = yaml.safe_load(stream)
    except yaml.YAMLError:
        logging.exception('Could not parse the spec file')
        raise
    except:
        logging.exception('Could not read the spec file')
        raise
    else:
        return spec_data


def _split_path_and_experiments(spec_path):
    # Split spec path by ':' (e.g., 'a/b:exp1' becomes ['a/b', 'exp1'])
    path_and_exp = spec_path.split(':')

    # Check whether there are experiments spec
    if len(path_and_exp) <= 1:
        path = path_and_exp[0]
        experiments = None
    elif len(path_and_exp) <= 2:
        path = path_and_exp[0]
        experiments = path_and_exp[1].split(',')
    else:
        error_message = 'There should be only one ":" in spec_path'
        logging.error(error_message)
        raise ValueError(error_message)

    # Return spec path and experiments spec
    return path, experiments


def _fill_missing_with_defaults(default_spec, user_spec):
    """ Fill missing values with default values.
    For example, default_spec = {'a': {'b': 3.14}}, user_spec = {}
    """
    # Set the keys to be targets of filling
    keys = [
        'name',
        'description',
        'before_all_experiments',
        'before_each_experiment',
        'experiments',
        'after_each_experiment',
        'after_all_experiments',
        'each_server/*',
        'servers',
        'requirements/*',
    ]

    # Iterate each key
    for key in keys:
        # Split the key by '/' into parts (e.g., 'a/b' becomes ['a', 'b'])
        parts = key.split('/')

        # Go inside the nested dict to assign the values
        user_parent = None

        default_value = default_spec
        user_value = user_spec

        for part in parts:
            if part == '*':
                # e.g., key = 'a/*', part = '*',
                # user_value = user_spec['a']

                # Assign each default value
                for default_k, default_v in default_value.items():
                    # e.g., default_k = 'b', default_v = 3.14

                    # Assign default value
                    user_value[default_k] = default_v
            else:
                # e.g., part = 'b'

                # Save the last user value as parent (e.g., user_spec['a'])
                user_parent = user_value

                # Get the values (e.g., default_spec['a'][part])
                default_value = default_value.get(part, {})
                user_value = user_value.get(part, {})

                # Check whether to set missing user dict
                if user_value == {}:
                    user_parent[part] = {}
                    user_value = user_parent.get(part, {})

        # Assign default value
        if part != '*':
            # e.g., part = 'b', user_parent = user_spec['a'],
            # default_value = 3.14

            # Get user value
            user_value = user_parent.get(part, None)

            # Assign the default value if user value is not specified
            user_parent[part] = user_value or default_value


def _filter_experiments(user_spec, experiments):
    # Check whether there are no experiments specification
    if experiments is None:
        return

    # Filter the experiments
    user_spec['experiments'] = list(filter(
        lambda x: x['name'] in experiments, user_spec['experiments']))

    # Log the filtering
    logging.info('Filtered experiments: {}'.format(experiments))
