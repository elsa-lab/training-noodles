import json
import logging


def init_logging(args):
    # Set logging formats
    logging_config = dict(format='%(asctime)-15s %(name)-5s %(levelname)-8s %(message)s',
                          datefmt='%Y-%m-%d %H:%M:%S')

    # Set logging level
    if args.debug:
        logging_config['level'] = logging.DEBUG
    else:
        logging_config['level'] = logging.INFO

    # Config logging
    logging.basicConfig(**logging_config)

    # Log verbose information
    if args.verbose:
        # Log verbose warning
        logging.warning('Verbose logging is on')

    # Log debug information
    if args.debug:
        # Log debug warning
        logging.warning('Debug logging is on')

        # Log arguments
        args_as_dict = vars(args)
        logging.debug('Arguments: {}'.format(json.dumps(args_as_dict)))
