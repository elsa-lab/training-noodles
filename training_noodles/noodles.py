from training_noodles.arguments import parse_args
from training_noodles.logger import init_logging
from training_noodles.spec import read_user_spec


def main():
    # Parse the arguments
    args = parse_args()

    # Initialize logging
    init_logging(args)

    # Read the spec
    user_spec = read_user_spec(args)


if __name__ == '__main__':
    main()
