import collections
import logging


def convert_values_to_strs(d):
    return {k: str(v) for k, v in d.items()}


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
        raise ValueError('Unknown type of input: {}'.format(type(x)))
