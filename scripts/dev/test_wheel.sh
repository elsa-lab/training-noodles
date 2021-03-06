#!/bin/bash
#
# Test the wheel file in a new Anaconda environment
#
# Arguments:
# $1: Wheel filename

# Handle errors
source scripts/dev/includes/error_handling.sh

# Include constants
source scripts/dev/includes/constants.sh

# Include test functions
source scripts/dev/includes/tests.sh

# Get arguments
WHEEL_FILENAME=$1

# Print the goal of this script
echo "Test the wheel file \"$WHEEL_FILENAME\""

# Test each Python version
for TEST_PYTHON_VERSION in "${TEST_PYTHON_VERSIONS[@]}"
do
    # Print the Python version
    echo "Test with Python $TEST_PYTHON_VERSION"

    # Clean old stuff
    clean_old_stuff

    # Set up test test environment
    set_up_test_env

    # Install the wheel file
    pip install "$WHEEL_FILENAME"

    # Run the tests
    run_tests

    # Tear down the test environment
    tear_down_test_env
done

# Print success message
echo "Successfully tested the wheel file \"$WHEEL_FILENAME\""
