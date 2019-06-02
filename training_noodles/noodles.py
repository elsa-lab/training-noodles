import logging
import sys

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

    # Build the runner
    runner = Runner(args.type, user_spec, verbose=args.verbose)

    # Start the runner
    runner.run()

    # Return success code
    return 0


if __name__ == '__main__':
    # Run main method
    status = main()

    # Exit with status
    sys.exit(status)
