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


def match_full(pattern, s):
    # Check whether the pattern is valid
    if not isinstance(pattern, str):
        return False

    # Convert the input to string
    s = str(s)

    # Find the matches
    m = re.match(pattern, s)

    # Check whether there are any matches
    if m is not None:
        # Check full match
        if len(m.group()) == len(s):
            return True

    # otherwise, it's not a full match
    return False


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
    # Create empty dict
    new_d = {}

    # Iterate each dict
    for d in ds:
        new_d.update({k: v for k, v in d.items() if k not in new_d})

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
