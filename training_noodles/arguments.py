import argparse


def parse_args():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Run noodles spec')

    # Command type
    parser.add_argument('type', type=str,
                        help='Command type (e.g., "run", "stop")')
    # Spec
    parser.add_argument('spec', type=str,
                        help='Path to the spec file' +
                        ' (e.g., "spec.yml", "spec.yml:exp1,exp2")')
    # Logging
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print out verbose messages')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Print out debug messages')
    parser.add_argument('-s', '--silent', action='store_true',
                        help='Silence all logging messages')

    # Parse the arguments
    args = parser.parse_args()

    return args
