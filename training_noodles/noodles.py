import logging

from training_noodles.arguments import parse_args
from training_noodles.logger import init_logging
from training_noodles.runner import Runner
from training_noodles.spec import read_user_spec


def main():
    # Parse the arguments
    args = parse_args()

    # Initialize logging
    init_logging(args)

    # Read the spec
    user_spec = read_user_spec(args)

    # Check the command type
    if args.command == 'run':
        runner = Runner(user_spec, verbose=args.verbose)
        runner.run()
    elif args.command == 'status':
        raise NotImplementedError()
    elif args.command == 'monitor':
        raise NotImplementedError()
    elif args.command == 'stop':
        raise NotImplementedError()
    elif args.command == 'download':
        raise NotImplementedError()
    elif args.command == 'upload':
        raise NotImplementedError()
    else:
        message = 'Unknown command type: {}'.format(args.command)
        logging.error(message)
        raise ValueError(message)


if __name__ == '__main__':
    main()
