import sys

from training_noodles.arguments import parse_args
from training_noodles.logging_utils import init_logging
from training_noodles.runner import Runner


def main():
    # Parse the arguments
    args = parse_args()

    # Initialize logging
    init_logging(args)

    # Build the runner
    runner = Runner(args.type, args.spec, verbose=args.verbose)

    # Start the runner
    runner.run()

    # Return the success code
    return 0


if __name__ == '__main__':
    # Run the main method
    status = main()

    # Exit with the status
    sys.exit(status)
