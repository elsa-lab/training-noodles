import ast
import collections
import datetime
import logging
import re
import time

import pkg_resources


def convert_unix_time_to_iso(t, tz=None):
    # Convert to datetime
    d = datetime.datetime.fromtimestamp(t, tz=tz)

    # Return ISO format
    return d.isoformat()


def convert_values_to_strs(d):
    return {k: str(v) for k, v in d.items()}


def get_resource_path(package, resource_name):
    # Build the requirement
    requirement = pkg_resources.Requirement.parse(package)

    # Get the resource filename and return
    return pkg_resources.resource_filename(requirement, resource_name)


def has_environment_variable(expr):
    # Set the pattern
    pattern = r'(\$.+)|(\${.+})'

    # Find if there is any environment variable
    m = re.search(pattern, expr)

    # Return the result
    return m is not None


def parse_requirement_expression(expr):
    # Set the pattern
    pattern = r'^(?P<operator>==|!=|<=|>=|<|>)(?P<value>.+)$'

    # Find the match
    m = re.fullmatch(pattern, expr)

    # Check if there is a match
    if m is None:
        # Return none
        return None
    else:
        # Get the operator and value
        operator = m.group('operator')
        value = m.group('value')

        # Try to parse the value
        try:
            value = ast.literal_eval(value)
        except:
            # Ignore the exception
            pass

        # Return the operator and value
        return {
            'operator': operator,
            'value': value,
        }


def split_by_scheme(s, schemes):
    """ Split the string by identifiable scheme.

    Scheme is only valid if it contains only word characters.

    Arguments:
        s (str): Input string which may contain scheme (e.g., "abc:123")
        schemes (list): List of identifiable schemes (str).

    Returns:
        (success (bool), scheme (str), follow (str))
        1. If there is unidentifiable scheme, "success" is False, Otherwise,
        "success" is True.
        2. "scheme" is set to one of identifiable scheme when there is any,
        otherwise it is None.
        3. "follow" is set to the string following the colon if there is any
        scheme, otherwise set to original "s". (e.g., "abc:123" -> "123",
        "456" -> "456")
    """
    # Split the string by colon
    parts = s.split(sep=':', maxsplit=1)

    # Check whether the first part is a scheme
    if len(parts) >= 2:
        # Check if the first part contains only word characters
        if re.match('^\\w+$', parts[0]) is None:
            return True, None, s
        else:
            # Check if the first part is in identifiable schemes
            if parts[0] in schemes:
                return True, parts[0], parts[1]
            else:
                return False, parts[0], parts[1]
    else:
        return True, None, s


def update_dict_with_missing(*ds):
    # Create an empty ordered dict
    new_d = collections.OrderedDict()

    # Iterate each dict
    for d in ds:
        # Iterate each item in the dict
        for k, v in d.items():
            # Add the item if the key doesn't exist in the new dict
            if k not in new_d:
                new_d[k] = v

    # Return the updated dict
    return new_d


def wrap_with_list(x):
    if isinstance(x, str):
        return [x]
    elif isinstance(x, list):
        return x
    else:
        message = 'Unknown type of input: {}'.format(type(x))
        logging.error(message)
        raise ValueError(message)
