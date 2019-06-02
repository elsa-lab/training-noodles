import logging


def convert_values_to_strs(d):
    return {k: str(v) for k, v in d.items()}


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
