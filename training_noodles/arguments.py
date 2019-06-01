import argparse


def parse_args():
    # Create an argument parser
    parser = argparse.ArgumentParser(
        description='Training with instant noodles')

    # Command packet type
    parser.add_argument('type', type=str,
                        help='Command packet type (e.g., "run", "stop")')
    # Spec
    parser.add_argument('spec', type=str,
                        help='Path to the spec file' +
                        ' (e.g., "spec.yml", "spec.yml:exp1,exp2")')
    # Logging
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print out verbose messages')
    # Debug
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Print out debug messages')

    # Parse the arguments
    args = parser.parse_args()

    return args
