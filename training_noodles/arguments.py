import argparse


def parse_args():
    # Create an argument parser
    parser = argparse.ArgumentParser(
        description='Training with instant noodles')

    # Command
    parser.add_argument('command', type=str,
                        help='Command ("run", "status", "monitor", "stop",' +
                        ' "download", "upload")')
    # Spec
    parser.add_argument('spec', type=str,
                        help='Path to the spec file and experiments' +
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
