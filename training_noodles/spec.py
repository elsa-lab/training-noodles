import json
import logging

import yaml

from training_noodles.utils import update_dict_with_missing


# Set the path to default spec
default_spec_path = 'training_noodles/specs/defaults.yml'

# Set root keys
root_keys = [
    'name',
    'description',
    'before_all_experiments/*',
    'before_each_experiment/*',
    'each_experiment/*',
    'experiments',
    'after_each_experiment/*',
    'after_all_experiments/*',
    'each_server/*',
    'servers',
    'requirements/*',
    'round_interval',
    'deployment_interval',
    'check_any_errors',
    'error_handlers',
]

# Set server spec keys
server_spec_keys = [
    '*'
]


def read_user_spec(args):
    # Split the spec into spec path and experiments spec
    user_spec_path, experiments = _split_path_and_experiments(args.spec)

    # Read the default spec
    default_spec = _read_spec(default_spec_path)

    # Read the user spec
    user_spec = _read_spec(user_spec_path)

    # Log the original user spec
    logging.debug('Original user spec->\n{}'.format(json.dumps(user_spec)))

    # Fill missing values with default values
    _fill_missing_with_defaults(default_spec, user_spec, root_keys)

    # Fill missing values in server specs
    _fill_missing_in_server_specs(user_spec)

    # Filter the experiments
    _filter_experiments(user_spec, experiments)

    # Log the processed user spec
    logging.debug('Processed user spec->\n{}'.format(json.dumps(user_spec)))

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


def _fill_missing_in_server_specs(user_spec):
    # Get "each server" spec
    each_server_spec = user_spec.get('each_server', {})

    # Get server specs
    servers_spec = user_spec.get('servers', [])

    # Iterate each server spec
    for server_spec in servers_spec:
        # Fill missing values
        _fill_missing_with_defaults(
            each_server_spec, server_spec, server_spec_keys)


def _fill_missing_with_defaults(default_spec, user_spec, keys):
    """ Fill missing values with default values.

    Examples:
    1. default_spec = {'a': {'pi': 3.14}}, user_spec = {'a': {'g': 9.8}}. The
    keys are ["a/pi"], then user_spec would become
    {'a': {'g': 9.8, 'pi': 3.14}}.
    2. default_spec = {'a': {'g': 9.8, 'pi': 3.14}}, user_spec = {}. The keys
    are ["a/*"], then user_spec would become {'a': {'g': 9.8, 'pi': 3.14}}.

    Arguments:
        default_spec (dict): Default spec.
        user_spec (dict): User spec.
        keys (list): List of keys (str).

    Returns:
        dict: User spec with missing keys filled from default spec.
    """
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

                # Update missing values
                updated_user_value = update_dict_with_missing(
                    user_value, default_value)

                for k, v in updated_user_value.items():
                    user_value[k] = v
            else:
                # e.g., part = 'b'

                # Save the last user value as parent (e.g., user_spec['a'])
                user_parent = user_value

                # Get the values (e.g., default_spec['a'][part])
                default_value = default_value.get(part, {})
                user_value = user_value.get(part, {})

                # Check whether to set missing user dict
                if user_value == {}:
                    # Set the children to empty dict
                    user_parent[part] = {}

                    # Set the user value to the created empty dict
                    user_value = user_parent.get(part, {})

        # Assign default value in last part
        if part != '*':
            # e.g., part = 'b', user_parent = user_spec['a'],
            # default_value = 3.14

            # Get user value
            user_value = user_parent.get(part, None)

            # Assign the default value if user value is not specified
            if not user_value:
                user_parent[part] = default_value


def _filter_experiments(user_spec, experiments):
    # Check whether there are no experiments specification
    if experiments is None:
        return

    # Filter the experiments
    user_spec['experiments'] = list(filter(
        lambda x: x['name'] in experiments, user_spec['experiments']))

    # Log the filtering
    logging.info('Filtered experiments: {}'.format(experiments))
